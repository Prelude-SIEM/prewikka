# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


from prewikka import view, Filter


class AlertFilterEditionParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("mode", str)
        self.optional("filter_name", str)
        self.optional("filter_comment", str, default="")
        self.optional("formula", str, default="")
        self.optional("save_as", str)
        
    def normalize(self):
        view.Parameters.normalize(self)
        
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
    view_name = "filter_edition"
    view_parameters = AlertFilterEditionParameters
    view_template = "FilterEdition"
    
    def _setCommon(self):
        self.dataset["filters"] = self.env.db.getAlertFilterNames(self.user.login)
        self.dataset["objects"] = ",".join(map(lambda x: '"%s"' % x, Filter.ALERT_OBJECTS))
        self.dataset["operators"] = ",".join(map(lambda x: '"%s"' % x, ("==", "!=", "<", "<=", ">", ">=")))
        self.dataset["elements"] = [ ]
        self.dataset["fltr.name"] = ""
        self.dataset["fltr.comment"] = ""
        self.dataset["formula"] = ""

    def _reload(self):
        for name, obj, operator, value in self.parameters.get("elements", [ ]):
            self.dataset["elements"].append(self._element(name, obj, operator, value))

        self.dataset["fltr.name"] = self.parameters.get("filter_name", "")
        self.dataset["fltr.comment"] = self.parameters.get("filter_comment", "")
        
    def _element(self, name, obj="", operator="", value=""):
        return {
            "name": name,
            "object": obj,
            "operator": operator,
            "value": value
            }

    def render_alert_filter_load(self):
        self._setCommon()
        
        if self.parameters.has_key("filter_name"):
            filter = self.env.db.getAlertFilter(self.user.login, self.parameters["filter_name"])
            self.dataset["fltr.name"] = filter.name
            self.dataset["fltr.comment"] = filter.comment
            self.dataset["formula"] = filter.formula
            names = filter.elements.keys()
            names.sort()
            for name in names:
                obj, operator, value = filter.elements[name]
                self.dataset["elements"].append(self._element(name, obj, operator, value))
        else:
            self.dataset["elements"].append(self._element("A"))
            self.dataset["fltr.name"] = ""
            self.dataset["fltr.comment"] = ""

    def render_alert_filter_delete(self):
        if self.parameters.has_key("filter_name"):
            self.env.db.deleteFilter(self.user.login, self.parameters["filter_name"])
        self._setCommon()
        self.dataset["elements"].append(self._element("A"))
        self.dataset["fltr.name"] = ""
        self.dataset["fltr.comment"] = ""
        
    def render_alert_filter_save(self):
        elements = { }
        for name, obj, operator, value in self.parameters["elements"]:
            elements[name] = (obj, operator, value)

        filter = Filter.AlertFilter(self.parameters["save_as"],
                                    self.parameters.get("filter_comment", ""),
                                    elements,
                                    self.parameters["formula"])

        self.env.db.setFilter(self.user.login, filter)

        self._setCommon()
        self._reload()

    def render(self):
        if self.parameters.get("mode", "load") == "load":
            self.render_alert_filter_load()
        elif self.parameters["mode"] == "save":
            self.render_alert_filter_save()
        elif self.parameters["mode"] == "delete":
            self.render_alert_filter_delete()
