# Copyright (C) 2004-2019 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources

from prewikka import database, error, hookmanager, resource, response, template, view
from prewikka.dataprovider import CriterionOperator
from prewikka.utils import AttrObj, json
from prewikka.utils.viewhelpers import GridParameters

from . import FilterPlugin


def _flatten(criterion):
    if not criterion.operator.is_boolean:
        return criterion

    ret = AttrObj(operator=criterion.operator, operands=[])

    left = _flatten(criterion.left)
    right = _flatten(criterion.right)

    for operand in (left, right):
        if operand.operator == criterion.operator:
            ret.operands += operand.operands
        else:
            ret.operands.append(operand)

    return ret


class Filter(object):
    def __init__(self, id_, name, category, description, criteria):
        self.id_ = id_
        self.name = name
        self.category = category
        self.description = description
        self.criteria = criteria

    def flatten_criteria(self):
        ret = {}
        for typ, criterion in self.criteria.items():
            crit = _flatten(criterion)
            if not crit.operator.is_boolean:
                crit = AttrObj(operator=CriterionOperator.AND, operands=[crit])

            ret[typ] = crit

        return ret


class FilterDatabase(database.DatabaseHelper):
    def get_filters(self, user, ftype=None):
        l = self.query("SELECT id, name, category, description, value FROM Prewikka_Filter "
                       "WHERE userid = %s ORDER BY name", user.id)

        l = next(hookmanager.trigger("HOOK_FILTER_LISTING", l), l)

        for id_, name, category, description, value in l:
            criteria = json.loads(value)
            if not ftype or ftype in criteria:
                yield Filter(id_, name, category, description, criteria)

    def get_filter(self, user, name):
        rows = self.query("SELECT id, category, description, value FROM Prewikka_Filter "
                          "WHERE userid = %s AND name = %s", user.id, name)

        if not rows:
            return None

        id_, category, description, value = rows[0]
        return Filter(id_, name, category, description, json.loads(value))

    def upsert_filter(self, user, filter_):
        values = (user.id, filter_.id_, filter_.name, filter_.category, filter_.description, json.dumps(filter_.criteria))
        self.upsert("Prewikka_Filter", ("userid", "id", "name", "category", "description", "value"), [values], pkey=("id",))

    def delete_filter(self, user, name=None):
        query = "SELECT id, name FROM Prewikka_Filter WHERE userid = %(user)s"
        if name:
            query += " AND name = %(name)s"

        rows = self.query(query, user=user.id, name=name)

        if rows:
            self.query("DELETE FROM Prewikka_Filter WHERE id IN %s", (row[0] for row in rows))

        return rows

    def get_categories(self, user):
        query = "SELECT category FROM Prewikka_Filter WHERE userid = %(user)s AND category IS NOT NULL GROUP BY category ORDER BY category"
        return [row[0] for row in self.query(query, user=user.id)]


class FilterView(FilterPlugin, view.View):
    view_permissions = [N_("IDMEF_VIEW")]
    plugin_htdocs = (("filter", pkg_resources.resource_filename(__name__, 'htdocs')),)
    _filter_menu_tmpl = template.PrewikkaTemplate(__name__, "templates/menu.mak")

    def __init__(self):
        view.View.__init__(self)
        self._db = FilterDatabase()

    def _get_types(self):
        for typ in sorted(env.dataprovider.get_types(public=True)):
            yield typ, _(env.dataprovider.get_label(typ))

    @view.route("/settings/filters", menu=(N_("Preferences"), N_("Filters")), help="#filters", parameters=GridParameters("filters"))
    def listing(self):
        dataset = {}
        data = []

        for fltr in self._db.get_filters(env.request.user):
            elem = {
                "id": fltr.name,
                "name": resource.HTMLNode(
                    "a", fltr.name,
                    href=url_for(".edit", name=fltr.name),
                    title=_("Filter %s") % fltr.name
                ),
                "category": fltr.category,
                "description": fltr.description
            }
            for typ in fltr.criteria:
                elem[typ] = True

            data.append(elem)

        dataset["data"] = data
        dataset["columns"] = self._get_types()

        return template.PrewikkaTemplate(__name__, "templates/filterlisting.mak").render(**dataset)

    @hookmanager.register("HOOK_USER_DELETE")
    def _user_delete(self, user):
        self._filter_delete(user)

    def _filter_delete(self, user, name=None):
        for fid, fname in self._db.delete_filter(user, name):
            list(hookmanager.trigger("HOOK_FILTER_DELETE", user, fname, fid))

    @hookmanager.register("HOOK_MAINMENU_PARAMETERS_REGISTER")
    def _filter_parameters_register(self, view):
        view.optional("filter", text_type, save=True)
        return ["filter"]

    @hookmanager.register("HOOK_DATAPROVIDER_CRITERIA_PREPARE")
    def _filter_get_criteria(self, ctype):
        if not env.request.has_menu:
            return

        fname = env.request.menu_parameters.get("filter")
        if not fname:
            return

        return self._filter_get_criteria_by_name(fname, ctype)

    @hookmanager.register("HOOK_FILTER_GET_CRITERIA")
    def _filter_get_criteria_by_name(self, fname, ctype, user=None):
        f = self._db.get_filter(user or env.request.user, fname)
        if not f:
            return

        return f.criteria.get(ctype)

    @hookmanager.register("HOOK_MAINMENU_EXTRA_CONTENT")
    def _filter_html_menu(self, ctype, parameters, **kwargs):
        filters = list(self._db.get_filters(env.request.user, ctype))

        current_filter = parameters.get("filter")
        if current_filter not in [x.name for x in filters]:
            current_filter = None

        filter_categories = {}
        for fltr in filters:
            filter_categories.setdefault(fltr.category, []).append(fltr)

        dset = self._filter_menu_tmpl.dataset(
            current_filter=current_filter,
            filter_categories=filter_categories,
            **kwargs
        )

        return resource.HTMLSource(dset.render())

    @hookmanager.register("HOOK_CHART_PREPARE")
    def _chart_prepare(self, query, options):
        filter_name = options.get("filter")
        if not filter_name:
            return

        c = self._filter_get_criteria_by_name(filter_name, query.datatype, options.get("owner"))
        if not c:
            raise error.PrewikkaUserError(N_("Filter error"), N_("Filter '%s' does not exist", filter_name))

        query.criteria &= c

    @view.route("/settings/filters/new", help="#filteredition")
    @view.route("/settings/filters/<name>/edit", help="#filteredition")
    def edit(self, name=None):
        if "duplicate" in env.request.parameters:
            name = env.request.parameters["duplicate"]

        dataset = {
            "fltr": AttrObj(id_="", name="", category="", description="", criteria={}),
            "categories": self._db.get_categories(env.request.user),
            "types": list(self._get_types())
        }

        if name:
            dataset["fltr"] = self._db.get_filter(env.request.user, name)
            dataset["fltr"].criteria = dataset["fltr"].flatten_criteria()

        if "duplicate" in env.request.parameters:
            dataset["fltr"].name = None

        return template.PrewikkaTemplate(__name__, "templates/filteredition.mak").render(**dataset)

    @view.route("/settings/filters/delete", methods=["POST"])
    def delete(self):
        for name in env.request.parameters.getlist("id"):
            self._filter_delete(env.request.user, name)

    @view.route("/settings/filters/save", methods=["POST"])
    def save(self):
        name = env.request.parameters.get("filter_name")
        old_name = env.request.parameters.get("filter_old_name")
        category = env.request.parameters.get("filter_category")
        description = env.request.parameters.get("filter_description")

        if not name:
            raise error.PrewikkaUserError(N_("Could not save filter"), N_("No name for this filter was provided"))

        criteria = dict(zip(
            env.request.parameters.getlist("filter_types"),
            (json.loads(c) for c in env.request.parameters.getlist("filter_criteria"))
        ))

        filter_ = self._db.get_filter(env.request.user, old_name)
        filter_id = filter_.id_ if filter_ else None

        # Ensure the filter name is not already used by this user
        if name != old_name and self._db.get_filter(env.request.user, name):
            raise error.PrewikkaUserError(N_("Could not save filter"), N_("The filter name is already used by another filter"))

        # Do not erase filter components if the dataprovider failed to load
        if filter_:
            new_criteria = filter_.criteria
            new_criteria.update(criteria)
            criteria = new_criteria

        criteria = dict((k, v) for k, v in criteria.items() if v is not None)
        self._db.upsert_filter(env.request.user, Filter(filter_id, name, category, description, criteria))

        return response.PrewikkaResponse({"type": "reload", "target": "#main_menu_ng", "options": {"filter": name}})
