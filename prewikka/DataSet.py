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


import sys

import prewikka.Action


class BaseDataSet:
    active_section = None
    tabs = None
    active_tab = None

    def __init__(self):
        self.document = { }
        self.document['title'] = "[PREWIKKA]"
        self.document['css_files'] = [ ]
        self.document['js_files'] = [ ]
        self.document['css_files'].append("lib/style.css")
        self.document['js_files'].append("lib/functions.js")
        self.info = { }
        self.menu_items = [ ]
        self.topmenu_items = [ ]
        self.topmenu_quick_accessors = [ ]
        self.referer = ""
        self.current = ""
        if self.tabs:
            self.addTabs(self.tabs)
        
    def setInfoSoftware(self, software):
        self.info['software'] = software

    def setInfoPlace(self, place):
        self.info['place'] = place

    def setInfoTitle(self, title):
        self.info['title'] = title

    def addSection(self, name, action):
        item = { }
        item["name"] = name
        if name == self.active_section:
            item["type"] = "active"
        else:
            item["type"] = "inactive"
            item["link"] = self.createLink(action)
        self.menu_items.append(item)
        
    def addSections(self, sections):
        for name, action in sections:
            self.addSection(name, action)

    def addTab(self, name, action):
        item = { }
        item["name"] = name
        item["link"] = self.createLink(action)
        item["type"] = ("inactive", "active")[name == self.active_tab]
        self.topmenu_items.append(item)

    def addTabs(self, tabs):
        for name, action in tabs:
            self.addTab(name, action)

    def addQuickAccessor(self, name, action, parameters):
        item = { }
        item["name"] = name
        item["link"] = self.createLink(action, parameters)
        self.topmenu_quick_accessors.append(item)
        
    def addQuickAccessors(self, accessors):
        for name, action, parameters in accessors:
            self.addQuickAccessor(name, action, parameters)
    
    def setConfiguration(self, configuration):
        pass
        
    def createLink(self, action_name, parameters=None):
        link = "?action=%s" % action_name
        if parameters:
            link += "&%s" % str(parameters)
        
        return link



class PropertiesChangeDataSet:
    def __init__(self, name, action_name):
        self.properties = [ ]
        self.hiddens = [ ]
        self.submit = name
        self.addHidden("action", action_name)

    def addHidden(self, name, value):
        self.hiddens.append([ name, value ])

    def _addProperty(self, type, name, parameter, value=None):
        property = { "type": type, "name": name, "parameter": parameter, "value": value }
        self.properties.append(property)

    def addTextProperty(self, name, parameter, value=None):
        self._addProperty("text", name, parameter, value)

    def addPasswordProperty(self, name, parameter):
        self._addProperty("password", name, parameter)

    def addBooleanProperty(self, name, parameter, value=False):
        self._addProperty("checkbox", name, parameter, value)



class ConfigDataSet(BaseDataSet):
    active_section = "Configuration"
    
    def setConfiguration(self, configuration):
        self.addTabs(configuration)



class DataSet(dict):
    def __setitem__(self, key, value):
        keys = key.split(".", 1)
        if len(keys) == 1:
            dict.__setitem__(self, key, value)
        else:
            key1, key2 = keys
            if not self.has_key(key1):
                dict.__setitem__(self, key1, DataSet())
            dict.__getitem__(self, key1)[key2] = value
    
    def __getitem__(self, key):
        try:
            keys = key.split(".", 1)
            if len(keys) == 1:
                return dict.__getitem__(self, key)
            return dict.__getitem__(self, keys[0])[keys[1]]
        except KeyError:
            return ""
