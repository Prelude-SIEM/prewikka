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

from templates.layouts.normal import Normal, Menu, TopMenu


class View:
    def __init__(self, core):
        self.core = core
        self.headers = { "Content-type": "text/html" }

    def build(self, data):
        pass

    def createLink(self, action, parameters=None):
        link = "index.py?action=%s" % action.getId()
        if parameters:
            link += "&%s" % str(parameters)
        return link
    
    def __str__(self):
        content = ""
        for key, value in self.headers.items():
            content += "%s: %s\r\n" % (key, value)
        return content + "\r\n"



class ErrorView(View):
    def build(self, message):
        self._message = message
    
    def __str__(self):
        return View.__str__(self) + "<h1>%s</h1>" % self._message



class NormalView(View):
    def __init__(self, core):
        View.__init__(self, core)
        self._software = core.interface.getSoftware()
        self._place = core.interface.getPlace()
        self._title = core.interface.getTitle()
        self._active_module = None
        self._active_section = None
        self._tabs = [ ]
        self._active_tab = None
        self._main_content = None

    def setActiveModule(self, module):
        self._active_module = module

    def setActiveSection(self, section):
        self._active_section = section

    def setTabs(self, tabs):
        self._tabs = tabs

    def setActiveTab(self, tab):
        self._active_tab = tab
    
    def build(self, data):
        self._main_content = self.buildMainContent(data)
        
    def __str__(self):
        headers = View.__str__(self)
        
        normal = Normal.Normal()
        normal.setSoftware(self._software)
        normal.setTitle(self._title)
        normal.setPlace(self._place)
        
        menu = Menu.Menu()
        for section, action in self.core.interface.getSections():
            if section == self._active_section:
                menu.setActiveItem(section)
            else:
                menu.setInactiveItem(section, self.createLink(action))
        normal.setMenu(str(menu))
        
        topmenu = TopMenu.TopMenu()
        for name, action in self._tabs:
            if name == self._active_tab:
                set_item = topmenu.setActiveItem
            else:
                set_item = topmenu.setInactiveItem
            set_item(name, self.createLink(action))
        
        normal.setTopMenu(str(topmenu))
        
        normal.setPage(self._main_content)
        
        return headers + str(normal)
