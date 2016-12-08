# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
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

import re

import pkg_resources
import prelude
from prewikka import database, error, hookmanager, resource, template, usergroup, utils, version, view
from prewikka.dataprovider import Criterion
from prewikka.utils import AttrObj, html, json

_OP_TBL   = { "AND": "&&", "OR": "||" }
_TYPE_TBL = { "generic": "alert", "alert": "alert", "heartbeat": "heartbeat" }


class Filter:
    def __init__(self, name, ftype, comment, elements, formula):
        self.name = name
        self.type = ftype
        self.comment = comment
        self.elements = elements
        self.formula = formula
        crit = prelude.IDMEFCriteria(self.get_criteria(self.type).to_string())

    def get_criteria(self, wtype):
        if self.type != "generic" and self.type != wtype:
            return None

        prev_op = None
        ret = Criterion()

        for i in re.finditer("(\w+)", self.formula):
            val = i.group(1)

            op = _OP_TBL.get(val.upper())
            if op:
                prev_op = op
                continue

            if not val in self.elements:
                raise error.PrewikkaUserError(_("Invalid filter element"),
                    N_("Invalid filter element '%s' referenced from filter formula", val))

            criteria, op, value = self.elements[val]
            criteria = ".".join((_TYPE_TBL[wtype], criteria))

            cur = Criterion(criteria, op, value)
            ret = Criterion(ret, prev_op, cur) if prev_op else cur

        return ret


class FilterDatabase(database.DatabaseHelper):
    def get_filter_list(self, user, ftype=None, name=None):

        type_str=""
        if ftype:
            type_str = " AND (type = %s OR type = 'generic')" % self.escape(ftype)

        l = map(lambda r: r[0], self.query("SELECT name FROM Prewikka_Filter WHERE userid = %s%s%s" % (self.escape(user.id), type_str, self._chk("name", name))))

        for i in hookmanager.trigger("HOOK_FILTER_LISTING", l):
            if i is not None:
                l = i

            continue

        return l

    @database.use_transaction
    def upsert_filter(self, user, filter):
        values = (user.id, filter.name, filter.type, filter.comment, filter.formula)

        fid = int(self.upsert("Prewikka_Filter", ("userid", "name", "type", "comment", "formula"), [values], pkey=("userid", "name"), returning=["id"])[0][0])
        upval = ([fid, name] + list(e) for name, e in filter.elements.items())

        self.upsert("Prewikka_Filter_Criterion", ("id", "name", "path", "operator", "value"), upval, pkey=("id", "name"), merge={"id": fid})

    def get_filter(self, user, name):
        rows = self.query("SELECT id, comment, formula, type FROM Prewikka_Filter WHERE userid = %s AND name = %s", user.id, name)
        if len(rows) == 0:
            return None

        id, comment, formula, ftype = rows[0]
        elements = { }

        rows = self.query("SELECT name, path, operator, value FROM Prewikka_Filter_Criterion WHERE id = %d", int(id))
        for element_name, path, operator, value in rows:
            elements[element_name] = path, operator, value

        return Filter(name, ftype, comment, elements, formula)

    def delete_filter(self, user, name=None):
        qstr = ""
        if name:
            qstr = " AND name = %s" % self.escape(name)

        rows = self.query("SELECT id FROM Prewikka_Filter WHERE userid = %s%s" % (self.escape(user.id), qstr))
        idlist = [ id[0] for id in rows ]

        if rows:
            lst = ", ".join(idlist)
            self.query("DELETE FROM Prewikka_Filter_Criterion WHERE Prewikka_Filter_Criterion.id IN (%s)" % lst)
            self.query("DELETE FROM Prewikka_Filter WHERE id IN (%s)" % lst)

        return idlist


class AlertFilterEditionParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("mode", text_type)
        self.optional("filter_name", text_type)
        self.optional("filter_comment", text_type, default="")
        self.optional("filter_formula", text_type, default="")
        self.optional("load", text_type)

    def normalize(self, *args, **kwargs):
        view.Parameters.normalize(self, *args, **kwargs)

        self["elements"] = [ ]
        for parameter in self.keys():
            idx = parameter.find("object_")
            if idx == -1:
                continue
            name = parameter.replace("object_", "", 1)
            self["elements"].append((name,
                                     self["object_%s" % name],
                                     self["operator_%s" % name],
                                     self.get("value_%s" % name, "")))



class AlertFilterEdition(view.View):
    plugin_name = "Filters management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Filters management page")
    plugin_database_branch = version.__branch__
    plugin_database_version = "0"

    view_name = N_("Filters")
    view_parameters = AlertFilterEditionParameters
    view_template = template.PrewikkaTemplate(__name__, "templates/filteredition.mak")
    view_section = N_("Settings")
    view_order = 1
    view_permissions = [ N_("IDMEF_VIEW") ]

    _filter_menu_tmpl = template.PrewikkaTemplate(__name__, "templates/menu.mak")

    @hookmanager.register("HOOK_USER_DELETE")
    def _user_delete(self, user):
        for i in self._db.get_filter_list(user):
            self._filter_delete(user, i)

    def _filter_delete(self, user, name):
        idlist = self._db.delete_filter(user, name)
        list(hookmanager.trigger("HOOK_FILTER_DELETE", user, name, idlist[0]))

    @hookmanager.register("HOOK_MAINMENU_PARAMETERS_REGISTER")
    def _filter_parameters_register(self, view):
        view.optional("filter", text_type, save=True)
        return ["filter"]

    @hookmanager.register("HOOK_DATAPROVIDER_CRITERIA_PREPARE")
    def _filter_get_criteria(self, criteria, ctype):
        menu = env.request.menu
        if not menu:
            return

        fname = env.request.parameters.get("filter")
        if not fname:
            return

        f = self._db.get_filter(env.request.user, fname)
        if not f:
            return

        f = f.get_criteria(ctype)
        if f:
            criteria += f

    @hookmanager.register("HOOK_MAINMENU_EXTRA_CONTENT")
    def _filter_html_menu(self, ctype):
        if ctype not in ("alert", "heartbeat"):
            return

        dset = self._filter_menu_tmpl.dataset()
        dset["current_filter"] = env.request.parameters.get("filter", "")
        dset["filter_list"] = self._db.get_filter_list(env.request.user, ctype)

        return resource.HTMLSource(dset.render())

    def __init__(self):
        view.View.__init__(self)
        self._db = FilterDatabase()

    def _flatten(self, rootcl):
        ret = []
        for subcl in rootcl:
            if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
                ret += self._flatten(subcl)
            else:
                ret.append(subcl.getPath(rootidx=1))
        return ret

    def _set_common(self):
        env.request.dataset["type"] = env.request.parameters.get("type", "filter")
        env.request.dataset["filter_list"] = self._db.get_filter_list(env.request.user)

        env.request.dataset["alert_objects"] = self._flatten(prelude.IDMEFClass("alert"))
        env.request.dataset["generic_objects"] = self._flatten(prelude.IDMEFClass("heartbeat"))

        env.request.dataset["operators"] = [
            ("=", _("Equal")),
            ("=*", _("Equal (case-insensitive)")),
            ("!=", _("Not equal")),
            ("!=*", _("Not equal (case-insensitive)")),
            ("~", _("Regular expression")),
            ("~*", _("Regular expression (case-insensitive)")),
            ("!~", _("Not regular expression")),
            ("!~*", _("Not regular expression (case-insensitive)")),
            ("<", _("Lesser than")),
            ("<=", _("Lesser or equal")),
            (">", _("Greater than")),
            (">=", _("Greater or equal")),
            ("<>", _("Substring")),
            ("<>*", _("Substring (case-insensitive)")),
            ("!<>", _("Not substring")),
            ("!<>*", _("Not substring (case-insensitive)"))]

        env.request.dataset["elements"] = [self._element("A")]
        env.request.dataset["fltr"] = AttrObj(name="", type="", comment="", formula="")

    def _reload(self):
        env.request.dataset["elements"] = []

        for name, obj, operator, value in env.request.parameters.get("elements", [ ]):
            env.request.dataset["elements"].append(self._element(name, obj, operator, value))

        for i in ("name", "type", "comment", "formula"):
            setattr(env.request.dataset["fltr"], i, env.request.parameters.get("filter_%s" % i, ""))

    def _element(self, name, obj="", operator="", value=""):
        return {
            "name": name,
            "object": obj,
            "operator": operator,
            "value": value
            }

    def _load(self):
        self._set_common()

        fname = env.request.parameters.get("filter_name")
        if fname:
            filter = self._db.get_filter(env.request.user, fname)

            for i in ("name", "type", "comment", "formula"):
                setattr(env.request.dataset["fltr"], i, getattr(filter, i))

            env.request.dataset["elements"] = []

            for name in sorted(filter.elements.keys()):
                obj, operator, value = filter.elements[name]
                env.request.dataset["elements"].append(self._element(name, obj, operator, value))

    def _delete(self):
        fname = env.request.parameters.get("filter_name")
        if fname:
            self._filter_delete(env.request.user, fname)

        self._set_common()

    def _save(self):
        elements = { }

        for name, obj, operator, value in env.request.parameters["elements"]:
            elements[name] = (obj, operator, value)
            if name not in env.request.parameters["filter_formula"]:
                raise error.PrewikkaUserError(_("Could not save Filter"), N_("No valid filter formula provided"))

        fname = env.request.parameters.get("filter_name")
        if not fname:
            raise error.PrewikkaUserError(_("Could not save Filter"), N_("No name for this filter was provided"))

        if not env.request.parameters["filter_formula"]:
            raise error.PrewikkaUserError(_("Could not save Filter"), N_("No valid filter formula provided"))

        if env.request.parameters.get("load") != fname and self._db.get_filter(env.request.user, fname):
            raise error.PrewikkaUserError(_("Could not save Filter"), N_("The filter name is already used by another filter"))

        fltr = Filter(fname,
                      env.request.parameters["filter_type"],
                      env.request.parameters.get("filter_comment", ""),
                      elements,
                      env.request.parameters["filter_formula"])

        self._db.upsert_filter(env.request.user, fltr)

        self._set_common()
        self._reload()


    def render(self):
        if env.request.parameters.get("mode", _("Load")) == _("Load"):
            self._load()

        elif env.request.parameters["mode"] == _("Save"):
            self._save()

        elif env.request.parameters["mode"] == _("Delete"):
            self._delete()

        env.request.dataset["elements"] = env.request.dataset["elements"]
