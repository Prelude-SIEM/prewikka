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

def template(name):
    return getattr(__import__("prewikka/templates/" + name), name)


    
class HTMLDocumentView(template("HTMLDocument")):
    def __init__(self, core):
        template("HTMLDocument").__init__(self)
        self._core = core
        self.document = { }
        self.document['title'] = "[PREWIKKA]"
        self.document['css_files'] = [ ]
        self.document['js_files'] = [ ]
        self.document['css_files'].append("lib/style.css")
        self.document['js_files'].append("lib/functions.js")
        self.info = { }
        self.info['software'] = core.interface.getSoftware()
        self.info['place'] = core.interface.getPlace()
        self.info['title'] = core.interface.getTitle()

    def createLink(self, action, parameters=None):
        from prewikka import Interface
        
        link = "?action=%s" % Interface.get_action_name(action)
        if parameters:
            link += "&%s" % str(parameters)
        return link



class NormalLayoutView(template("NormalLayout")):
    action_section = None
    tabs = None
    active_tab = None
    
    def __init__(self, core):
        template("NormalLayout").__init__(self, core)
        self.topmenu_items = [ ]
        self.topmenu_special_items = [ ]
        self.menu_items = [ ]
        
        for section, action in self._core.interface.getSections():
            item = { }
            item["name"] = section
            if section == self.active_section:
                item["type"] = "active"
            else:
                item["type"] = "inactive"
                item["link"] = self.createLink(action)
            self.menu_items.append(item)

        for name, action in self.tabs:
            item = { }
            item["name"] = name
            item["link"] = self.createLink(action)
            item["type"] = ("inactive", "active")[name == self.active_tab]
            self.topmenu_items.append(item)
            
        for name, action, parameters in self._core.interface.getSpecialActions():
            item = { }
            item["name"] = name
            item["link"] = self.createLink(action, parameters)
            self.topmenu_special_items.append(item)



class PropertiesChangeView(template("PropertiesChange")):
    def __init__(self, core, action_name, action):
        template("PropertiesChange").__init__(self, core)
        self.properties = [ ]
        self.submit = action_name
        self.hiddens = [ ]
        from prewikka import Interface
        self.addHidden("action", Interface.get_action_name(action))

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



class NormalView(NormalLayoutView):
    pass



class TopView:
    pass
