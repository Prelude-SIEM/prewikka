# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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
from prewikka.utils import AttrObj, json

from . import FilterPlugin


_TYPES = ["alert", "heartbeat", "log", "ticket"]


def _flatten(criterion):
    if criterion.operator not in ("&&", "||"):
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
    def __init__(self, name, description, criteria):
        self.name = name
        self.description = description
        self.criteria = criteria

    def flatten_criteria(self):
        ret = {}
        for typ, criterion in self.criteria.items():
            crit = _flatten(criterion)
            if crit.operator not in ("&&", "||"):
                crit = AttrObj(operator="&&", operands=[crit])

            ret[typ] = crit

        return ret


class FilterDatabase(database.DatabaseHelper):
    @database.use_transaction
    def get_filters(self, user, ftype=None):
        l = self.query("SELECT name, description, value FROM Prewikka_Filter "
                       "WHERE userid = %s", user.id)

        l = next(hookmanager.trigger("HOOK_FILTER_LISTING", l), l)

        for name, description, value in l:
            criteria = json.loads(value)
            if not ftype or ftype in criteria:
                yield Filter(name, description, criteria)

    def get_filter(self, user, name):
        rows = self.query("SELECT description, value FROM Prewikka_Filter "
                          "WHERE userid = %s AND name = %s", user.id, name)
        if not rows:
            return None

        description, value = rows[0]
        return Filter(name, description, json.loads(value))

    def upsert_filter(self, user, filter):
        values = (user.id, filter.name, filter.description, json.dumps(filter.criteria))
        self.upsert("Prewikka_Filter", ("userid", "name", "description", "value"), [values], pkey=("userid", "name"), returning=["id"])

    @database.use_transaction
    def delete_filter(self, user, name=None):
        query = "SELECT id, name FROM Prewikka_Filter WHERE userid = %(user)s"
        if name:
            query += " AND name = %(name)s"

        rows = self.query(query, user=user.id, name=name)

        if rows:
            self.query("DELETE FROM Prewikka_Filter WHERE id IN %s", (row[0] for row in rows))

        return rows


class FilterView(FilterPlugin, view.View):
    view_permissions = [N_("IDMEF_VIEW")]
    plugin_htdocs = (("filter", pkg_resources.resource_filename(__name__, 'htdocs')),)
    _filter_menu_tmpl = template.PrewikkaTemplate(__name__, "templates/menu.mak")

    def __init__(self):
        view.View.__init__(self)
        self._db = FilterDatabase()

    def _get_types(self):
        for typ in _TYPES:
            if env.dataprovider.has_type(typ):
                yield typ, _(env.dataprovider.get_label(typ))

    @view.route("/settings/filters", menu=(N_("Preferences"), N_("Filters")), help="#filters")
    def listing(self):
        dataset = {}
        data = []

        for fltr in self._db.get_filters(env.request.user):
            elem = {
                "id": fltr.name,
                "name": fltr.name,
                "description": fltr.description,
                "_link": url_for(".edit", name=fltr.name),
                "_title": _("Filter %s") % fltr.name
            }
            for typ in fltr.criteria:
                elem[typ] = True

            data.append(elem)

        dataset["data"] = data
        dataset["col_idents"], dataset["col_names"] = zip(*self._get_types())

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
        if not env.request.menu:
            return

        fname = env.request.parameters.get("filter")
        if not fname:
            return

        f = self._db.get_filter(env.request.user, fname)
        if not f:
            return

        return f.criteria.get(ctype)

    @hookmanager.register("HOOK_MAINMENU_EXTRA_CONTENT")
    def _filter_html_menu(self, ctype):
        dset = self._filter_menu_tmpl.dataset()
        dset["current_filter"] = env.request.parameters.get("filter", "")
        dset["filter_list"] = (f.name for f in self._db.get_filters(env.request.user, ctype))

        return resource.HTMLSource(dset.render())

    @view.route("/settings/filters/new", help="#filteredition")
    @view.route("/settings/filters/<name>/edit", help="#filteredition")
    def edit(self, name=None):
        if "duplicate" in env.request.parameters:
            name = env.request.parameters["duplicate"]

        dataset = {
            "fltr": AttrObj(name="", description="", criteria={}),
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
        for name in env.request.parameters.getlist("id[]"):
            self._filter_delete(env.request.user, name)

    @view.route("/settings/filters/save", methods=["POST"])
    def save(self):
        fname = env.request.parameters.get("filter_name")
        if not fname:
            raise error.PrewikkaUserError(N_("Could not save filter"), N_("No name for this filter was provided"))

        criteria = dict(zip(
            env.request.parameters.getlist("filter_types"),
            (json.loads(c) for c in env.request.parameters.getlist("filter_criteria"))
        ))

        fltr = self._db.get_filter(env.request.user, fname)
        if fltr:
            if env.request.parameters.get("filter_id") != fname:
                raise error.PrewikkaUserError(N_("Could not save filter"), N_("The filter name is already used by another filter"))

            # Do not erase filter components if the dataprovider failed to load
            new_criteria = fltr.criteria
            new_criteria.update(criteria)
            criteria = new_criteria

        criteria = dict((k, v) for k, v in criteria.items() if v is not None)

        description = env.request.parameters.get("filter_description", "")
        self._db.upsert_filter(env.request.user, Filter(fname, description, criteria))

        return response.PrewikkaDirectResponse({"type": "ajax-reload"})
