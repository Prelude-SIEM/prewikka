# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import prelude, re
from prewikka import view, error, usergroup, template, database, utils, version, env
from . import templates


class Filter:
    _typetbl = { "generic": "alert", "alert": "alert", "heartbeat": "heartbeat" }

    def __init__(self, name, ftype, comment, elements, formula):
        self.name = name
        self.type = ftype
        self.comment = comment
        self.elements = elements
        self.formula = formula
        crit = prelude.IDMEFCriteria(str(self))

    def _replace(self, element):
        element = element.group(1)
        if element in ("and", "AND", "&&"):
            return "&&"

        if element in ("or", "OR", "||"):
            return "||"

        if not element in self.elements:
            raise error.PrewikkaUserError(_("Invalid filter element"), _("Invalid filter element '%s' referenced from filter formula") % element)

        prev_val = self.elements[element][2]
        elements = self.elements[element]
        for i in env.hookmgr.trigger("HOOK_FILTER_CRITERIA_LOAD", elements):
            if i:
                elements = i

        criteria, operator, value = elements
        if value == prev_val:
            value = "'%s'" % utils.escape_criteria(utils.filter_value_adjust(operator, value))

        if self.type:
            criteria = ".".join((self._typetbl[self.type], criteria))

        return " ".join((criteria, operator, value))

    def __str__(self):
        return re.sub("(\w+)", self._replace, self.formula)


    def get_criteria_cast(self, wanted_type):
        if self.type != "generic" and self.type != wanted_type:
            return None

        old_type = self.type
        self.type = wanted_type
        fstr = str(self)
        self.type = old_type

        return fstr


class FilterDatabase(database.DatabaseHelper):
    def get_filter_list(self, user, ftype=None, name=None):

        type_str=""
        if ftype:
            type_str = " AND (type = %s OR type = 'generic')" % self.escape(ftype)

        l = map(lambda r: r[0], self.query("SELECT name FROM Prewikka_Filter WHERE userid = %s%s%s" % (self.escape(user.id), type_str, self._chk("name", name))))

        for i in env.hookmgr.trigger("HOOK_FILTER_LISTING", l):
            if i is not None:
                l = i

            continue

        return l

    def get_alert_filter(self, user):
        return self.get_filter_list(user, "alert")

    def get_heartbeat_filter(self, user):
        return self.get_filter_list(user, "heartbeat")

    @database.use_transaction
    def set_filter(self, user, filter):
        self.query("INSERT INTO Prewikka_Filter (userid, type, name, comment, formula) VALUES (%s, %s, %s, %s, %s)" %
                   (self.escape(user.id), self.escape(filter.type), self.escape(filter.name), self.escape(filter.comment), self.escape(filter.formula)))
        id = int(self.query("SELECT MAX(id) FROM Prewikka_Filter")[0][0])
        for name, element in filter.elements.items():
            self.query("INSERT INTO Prewikka_Filter_Criterion (id, name, path, operator, value) VALUES (%d, %s, %s, %s, %s)" %
                       ((id, self.escape(name)) + tuple([ self.escape(e) for e in element ])))

    def get_filter(self, user, name):
        rows = self.query("SELECT id, comment, formula, type FROM Prewikka_Filter WHERE userid = %s AND name = %s" %
                          (self.escape(user.id), self.escape(name)))
        if len(rows) == 0:
            return None

        id, comment, formula, ftype = rows[0]
        elements = { }

        rows = self.query("SELECT name, path, operator, value FROM Prewikka_Filter_Criterion WHERE id = %d" % int(id))
        for element_name, path, operator, value in rows:
            elements[element_name] = path, operator, value

        return Filter(name, ftype, comment, elements, formula)

    def delete_filter(self, user, name=None):
        qstr = ""
        if name:
            qstr = " AND name = %s" % self.escape(name)

        rows = self.query("SELECT id FROM Prewikka_Filter WHERE userid = %s%s" % (self.escape(user.id), qstr))
        if len(rows) > 0:
            lst = ", ".join([ id[0] for id in rows ])
            self.query("DELETE FROM Prewikka_Filter_Criterion WHERE Prewikka_Filter_Criterion.id IN (%s)" % lst)
            self.query("DELETE FROM Prewikka_Filter WHERE id IN (%s)" % lst)



class AlertFilterEditionParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("mode", str)
        self.optional("filter_name", str)
        self.optional("filter_comment", str, default="")
        self.optional("filter_formula", str, default="")

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
    view_template = templates.FilterEdition
    view_section = N_("Settings")
    view_order = 1
    view_permissions = [ usergroup.PERM_IDMEF_VIEW ]
    example_formula = N_("Example: (A AND B) OR (C AND D)")

    def _user_delete_hook(self, user):
        for i in self._db.get_filter_list(user):
            self._filter_delete(user, i)

    def _filter_delete(self, user, name):
        self._db.delete_filter(user, name)

        for i in env.hookmgr.trigger("HOOK_FILTER_DELETE", user, name):
            continue

    def _filter_parameters_register_hook(self, view):
        view.optional("filter", str, save=True)
        return ["filter"]

    def _filter_get_criteria_hook(self, menuview, ctype):
        if not "filter" in menuview.parameters:
            return None

        filter = self._db.get_filter(menuview.user, menuview.parameters["filter"])
        if filter:
            return filter.get_criteria_cast(ctype)

    def _filter_html_menu_hook(self, view, ctype):
        tmpl = template.PrewikkaTemplate(templates.menu)

        tmpl["current_filter"] = view.parameters.get("filter", "")
        if ctype == "alert":
            tmpl["filters"] = self._db.get_alert_filter(view.user)
        else:
            tmpl["filters"] = self._db.get_heartbeat_filter(view.user)

        return tmpl.render()

    def __init__(self):
        view.View.__init__(self)
        self._db = FilterDatabase()

        env.hookmgr.declare("HOOK_FILTER_DELETE")
        env.hookmgr.declare("HOOK_FILTER_LISTING")
        env.hookmgr.declare_once("HOOK_FILTER_CRITERIA_LOAD")

        env.hookmgr.register("HOOK_MAINMENU_PARAMETERS_REGISTER", self._filter_parameters_register_hook)
        env.hookmgr.register("HOOK_MAINMENU_GET_CRITERIA", self._filter_get_criteria_hook)
        env.hookmgr.register("HOOK_MAINMENU_EXTRA_CONTENT", self._filter_html_menu_hook)
        env.hookmgr.register("HOOK_USER_DELETE", self._user_delete_hook)

    def _flatten(self, rootcl):
        ret = []
        for subcl in rootcl:
            if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
                ret += self._flatten(subcl)
            else:
                ret.append(subcl.getPath(rootidx=1))
        return ret

    def _set_common(self):
        self.dataset["type"] = self.parameters.get("type", "filter")
        self.dataset["filters"] = self._db.get_filter_list(self.user)

        self.dataset["alert_objects"] = self._flatten(prelude.IDMEFClass("alert"))
        self.dataset["generic_objects"] = self._flatten(prelude.IDMEFClass("heartbeat"))

        self.dataset["operators"] = ["=", "=*", "!=", "!=*", "~", "~*",
                                     "!~", "!~*", "<", "<=", ">", ">=",
                                     "<>", "<>*", "!<>", "!<>*"]

        self.dataset["elements"] = [self._element("A")]
        self.dataset["fltr.name"] = ""
        self.dataset["fltr.type"] = ""
        self.dataset["fltr.comment"] = ""
        self.dataset["fltr.formula"] = _(self.example_formula)

    def _reload(self):
        self.dataset["elements"] = []

        for name, obj, operator, value in self.parameters.get("elements", [ ]):
            self.dataset["elements"].append(self._element(name, obj, operator, value))

        self.dataset["fltr.type"] = self.parameters.get("filter_type", "")
        self.dataset["fltr.name"] = self.parameters.get("filter_name", "")
        self.dataset["fltr.comment"] = self.parameters.get("filter_comment", "")
        self.dataset["fltr.formula"] = self.parameters["filter_formula"]

    def _element(self, name, obj="", operator="", value=""):
        return {
            "name": name,
            "object": obj,
            "operator": operator,
            "value": value
            }

    def _load(self):
        self._set_common()

        fname = self.parameters.get("filter_name")
        if fname:
            filter = self._db.get_filter(self.user, fname)

            self.dataset["fltr.type"] = filter.type
            self.dataset["fltr.name"] = filter.name
            self.dataset["fltr.comment"] = filter.comment
            self.dataset["fltr.formula"] = filter.formula
            self.dataset["elements"] = []

            for name in sorted(filter.elements.keys()):
                obj, operator, value = filter.elements[name]
                self.dataset["elements"].append(self._element(name, obj, operator, value))

    def _delete(self):
        fname = self.parameters.get("filter_name")
        if fname:
            self._filter_delete(self.user, fname)

        self._set_common()

    def _save(self):
        elements = { }

        for name, obj, operator, value in self.parameters["elements"]:
            elements[name] = (obj, operator, value)
            if name not in self.parameters["filter_formula"]:
                raise error.PrewikkaUserError(_("Could not save Filter"), _("No valid filter formula provided"))

        fname = self.parameters.get("filter_name")
        if not fname:
            raise error.PrewikkaUserError(_("Could not save Filter"), _("No name for this filter was provided"))

        if self.parameters["filter_formula"] == _(self.example_formula):
            raise error.PrewikkaUserError(_("Could not save Filter"), _("No valid filter formula provided"))

        fltr = Filter(fname,
                      self.parameters["filter_type"],
                      self.parameters.get("filter_comment", ""),
                      elements,
                      self.parameters["filter_formula"])

        self._db.delete_filter(self.user, fltr.name)
        self._db.set_filter(self.user, fltr)

        self._set_common()
        self._reload()


    def render(self):
        if self.parameters.get("mode", _("Load")) == _("Load"):
            self._load()

        elif self.parameters["mode"] == _("Save"):
            self._save()

        elif self.parameters["mode"] == _("Delete"):
            self._delete()
