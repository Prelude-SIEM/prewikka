#from layout import layoutManager
from templates.layouts.normal import Normal, Menu, TopMenu
import core


class Interface:
    def __init__(self, core, config, data):
        self._core = core
        self._config = config
        self._data = data
        self.headers = { "Content-type": "text/html" }

    def init(self):
        pass

    def build(self):
        pass

    def __str__(self):
        content = ""
        for key, value in self.headers.items():
            content += "%s: %s\r\n" % (key, value)
        return content + "\r\n"



class NormalInterface(Interface):
    def init(self):
        self._module_names = self._core.getContentModuleNames()
        self._software = self._config.get("software", "Prewikka")
        self._place = self._config.get("place", "")
        self._title = self._config.get("title", "Prelude management")
        self._module_name = None
        self._tabs = [ ]
        self._active_tab = None
        self._main_content = ""

    def setModuleName(self, name):
        self._module_name = name

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
        for module in self._module_names:
            if module == self._module_name:
                menu.setActiveItem(module)
            else:
                request.module = module
                menu.setInactiveItem(module, str(request))
        normal.setMenu(str(menu))

        topmenu = TopMenu.TopMenu()
        request.module = self._module_name
        for name, action in self._tabs:
            if name == self._active_tab:
                topmenu.setActiveItem(name)
            else:
                request.action = action
                topmenu.setInactiveItem(name, str(request))
        normal.setTopMenu(str(topmenu))

        normal.setPage(self._main_content)

        return headers + str(normal)
