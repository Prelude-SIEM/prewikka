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


def get_next_filter_element_name(name):
    return chr(ord(name) + 1)



class FilterLoadParameters(view.Parameters):
    def register(self):
        self.mandatory("filter_name", str)



class FilterEditionParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("filter_name", str)
        self.optional("filter_comment", str)
        self.optional("formula", str)
        
    def normalize(self):
        view.Parameters.normalize(self)
        
        self["elements"] = [ ]
        name = "A"
        while True:
            if not self.has_key("object_%s" % name):
                break
            self["elements"].append((name,
                                     self["object_%s" % name],
                                     self["operator_%s" % name],
                                     self.get("value_%s" % name, "")))
            name = get_next_filter_element_name(name)



class FilterSaveParameters(FilterEditionParameters):
    def register(self):
        FilterEditParameters.register(self)
        self.mandatory("filter_name", str)



class AlertFilterEdition(view.Views):
    view_slots = {
        "alert_filter_edition": { "parameters": FilterEditionParameters,
                                  "permissions": [ ],
                                  "template": "FilterEdition" },
        "alert_filter_load": { "parameters": FilterLoadParameters,
                               "permissions": [ ],
                               "template": "FilterEdition" }
        }

    def _setCommon(self):
        self.dataset["filters"] = self.env.storage.getAlertFilters(self.user.login)
        self.dataset["objects"] = Filter.ALERT_OBJECTS
        self.dataset["operators"] = ("==", "!=", "<", "<=", ">", ">=")
        self.dataset["elements"] = [ ]
        self.dataset["fltr.name"] = ""
        self.dataset["fltr.comment"] = ""
        self.dataset["formula"] = ""
        
    def _element(self, name, obj="", operator="", value=""):
        return {
            "name": name,
            "object": obj,
            "operator": operator,
            "value": value
            }

    def _addEmptyElement(self, elements):
        if elements:
            name = get_next_filter_element_name(elements[-1]["name"])
        else:
            name = "A"

        elements.append(self._element(name))

    def _reloadForm(self):
        self._setCommon()
        
        name = "A"
        for name, obj, operator, value in self.parameters["elements"]:
            self.dataset["elements"].append(self._element(name, obj, operator, value))
            name = get_next_filter_element_name(name)

        if not self.dataset["elements"]:
            self._addEmptyElement(self.dataset["elements"])

        self.dataset["fltr.name"] = self.parameters.get("filter_name", "")
        self.dataset["fltr.comment"] = self.parameters.get("filter_comment", "")

    def render_alert_filter_edition(self):
        self._reloadForm()
        
        parameters = self.parameters.keys()
        if "save" in parameters:
            self.save()
        elif "new_element" in parameters:
            self._addEmptyElement(self.dataset["elements"])

        self._setCommon()

    def render_alert_filter_load(self):
        self._setCommon()
        filter = self.env.storage.getAlertFilter(self.user.login, self.parameters["filter_name"])
        self.dataset["fltr.name"] = filter.name
        self.dataset["fltr.comment"] = filter.comment
        self.dataset["formula"] = filter.formula
        names = filter.elements.keys()
        names.sort()
        for name in names:
            obj, operator, value = filter.elements[name]
            self.dataset["elements"].append(self._element(name, obj, operator, value))

    def save(self):
        elements = { }
        for name, obj, operator, value in self.parameters["elements"]:
            elements[name] = (obj, operator, value)

        filter = Filter.AlertFilter(self.parameters["filter_name"],
                                    self.parameters.get("filter_comment", ""),
                                    elements,
                                    self.parameters["formula"])

        self.env.storage.setFilter(self.user.login, filter)
