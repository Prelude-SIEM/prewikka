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

from prewikka.templates import TopLayout, NormalLayout


class View:
    def __init__(self, core):
        self.core = core
        self._title = None
        self._css_files = [ ]
        self._javascript_files = [ ]
        self._content = ""
        
    def setTitle(self, title):
        self._title = title

    def addCss(self, css_file):
        self._css_files.append(css_file)
    
    def addJavascript(self, javascript_file):
        self._javascript_files.append(javascript_file)
    
    def build(self, content):
        self._content = content
        
    def createLink(self, action, parameters=None):
        link = "?action=%s" % action.getName()
        if parameters:
            link += "&%s" % str(parameters)
        return link
    
    def __str__(self):
        content = """
        <!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Transitional//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd'>
        <html xmlns='http://www.w3.org/1999/xhtml'>
        <head>"""
        if self._title:
            title = "[PREWIKKA] " + self._title
        else:
            title = "PREWIKKA"
        content += "<title>%s</title>" % title
        content += "<meta http-equiv='Content-Type' content='text/html; charset=iso-8859-1'/>"
        for css_file in self._css_files:
            content += "<link rel='stylesheet' href='%s' type='text/css'/>" % css_file
        for javascript_file in self._javascript_files:
            content += "<script src='%s' type='text/javascript'></script>" % javascript_file
        content += "</head>"
        content += self._content
        content += "</html>"
        
        return content



class TopView(View):
    def build(self, content):
        self.addCss("lib/style.css")
        self.addJavascript("lib/functions.js")
        interface = self.core.interface
        top = TopLayout.TopLayout()
        top.setSoftware(interface.getSoftware())
        top.setPlace(interface.getPlace())
        top.setTitle(interface.getTitle())
        top.setContent(content)
        View.build(self, str(top))



class ErrorView(View):
    def build(self, message):
        View.build(self, "<h1>%s</h1>" % message)



class NormalView(TopView):
    def __init__(self, core):
        View.__init__(self, core)
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
        normal = NormalLayout.NormalLayout()

        for section, action in self.core.interface.getSections():
            if section == self._active_section:
                normal.addActiveMenuEntry(section)
            else:
                normal.addInactiveMenuEntry(section, self.createLink(action))
        
        for tab, action in self._tabs:
            if tab == self._active_tab:
                set_tab = normal.addActiveTabEntry
            else:
                set_tab = normal.addInactiveTabEntry
            set_tab(tab, self.createLink(action))

        normal.setContent(self.buildMainContent(data))

        return TopView.build(self, str(normal))
