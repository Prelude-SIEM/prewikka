import sys

from templates.layouts.normal import Normal, Menu, TopMenu
import Core


class View:
    def __init__(self, core, data):
        self._core = core
        self._data = data
        self.headers = { "Content-type": "text/html" }

    def init(self):
        pass

    def build(self):
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
    def __str__(self):
        return View.__str__(self) + "<h1>%s</h1>" % self._data



class NormalView(View):
    def init(self):
        self._software = self._core.interface.getSoftware()
        self._place = self._core.interface.getPlace()
        self._title = self._core.interface.getTitle()
        self._active_module = None
        self._active_section = None
        self._tabs = [ ]
        self._active_tab = None
        self._main_content = ""

    def setActiveModule(self, module):
        self._active_module = module

    def setActiveSection(self, section):
        self._active_section = section

    def setTabs(self, tabs):
        self._tabs = tabs

    def setActiveTab(self, tab):
        self._active_tab = tab

    def setMainContent(self, content):
        self._main_content = content

    def __str__(self):
        headers = View.__str__(self)
        
        normal = Normal.Normal()
        normal.setSoftware(self._software)
        normal.setTitle(self._title)
        normal.setPlace(self._place)
        
        menu = Menu.Menu()
        for section, action in self._core.interface.getSections():
            if section == self._active_section:
                menu.setActiveItem(section)
            else:
                menu.setInactiveItem(section, self.createLink(action))
        normal.setMenu(str(menu))
        
        topmenu = TopMenu.TopMenu()
        for name, action in self._tabs:
            if name == self._active_tab:
                topmenu.setActiveItem(name)
            else:
                topmenu.setInactiveItem(name, self.createLink(action))
        normal.setTopMenu(str(topmenu))
        
        normal.setPage(self._main_content)
        
        return headers + str(normal)
