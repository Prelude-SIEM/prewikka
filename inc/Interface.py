#from layout import layoutManager
import sys

from templates.layouts.normal import Normal, Menu, TopMenu
import core


class Interface:
    def __init__(self, core, config, request, data):
        self._core = core
        self._config = config
        self._request = request
        self._data = data
        self.headers = { "Content-type": "text/html" }

    def init(self):
        pass

    def build(self):
        pass

    def createLink(self, request):
        return "index.py?%s" % str(request)

    def __str__(self):
        content = ""
        for key, value in self.headers.items():
            content += "%s: %s\r\n" % (key, value)
        return content + "\r\n"


class ErrorInterface(Interface):
    def __str__(self):
        return Interface.__str__(self) + "<h1>%s</h1>" % self._data



class NormalInterface(Interface):
    def init(self):
        self._software = self._config.get("software", "Prewikka")
        self._place = self._config.get("place", "")
        self._title = self._config.get("title", "Prelude management")
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
        headers = Interface.__str__(self)
        
        request = core.CoreRequest()
        
        normal = Normal.Normal()
        normal.setSoftware(self._software)
        normal.setTitle(self._title)
        normal.setPlace(self._place)

        menu = Menu.Menu()
        for module in self._core.getContentModuleNames():
            for section, action in self._core.content_modules[module].getSections():
                if section == self._active_section:
                    menu.setActiveItem(section)
                else:
                    request.module = module
                    request.action = action
                    menu.setInactiveItem(section, self.createLink(request))
        normal.setMenu(str(menu))

        topmenu = TopMenu.TopMenu()
        request.module = self._active_module
        for name, action in self._tabs:
            if name == self._active_tab:
                topmenu.setActiveItem(name)
            else:
                request.action = action
                topmenu.setInactiveItem(name, self.createLink(request))
        normal.setTopMenu(str(topmenu))

        normal.setPage(self._main_content)

        return headers + str(normal)
