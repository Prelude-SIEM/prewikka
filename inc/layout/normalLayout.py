#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from genericLayout import genericLayout
from templates import NormalLayout, Menu, TopMenu

class normalLayout(genericLayout):

    def __init__(self, views, query):
        self._views = views
        self._query = query
        layout = NormalLayout.NormalLayout()

        if "help" in views:
            layout.setHelp(views["help"])

        if "modules" in views and "module" in views:
            layout.setMenu(self._getMenu(views["modules"], views['sid']))

        if "module" in views and "pages" in views:
            layout.setTopMenu(self._getPageMenu(views["pages"], views["active"], views["module"], views['sid']))

        if "main" in views:
            layout.setPage(views["main"])
        
        if "software" in views:
            layout.setSoftware(views["software"])
        
        if "title" in views:
            layout.setTitle(views["title"])
        
        if "place" in views:
            layout.setPlace(views["place"])
            
        self._output = str(layout)

    def __str__(self):
        return self._output

    def _getPageMenu(self, pages, active, module, sid):
        menu = TopMenu.TopMenu()
        for page in pages:
            if page == active:
                menu.setActiveItem(page)
            else:
                menu.setInactiveItem(page, str(self._query))
        
        return str(menu)

    def _getMenu(self, modules, sid):
        menu = Menu.Menu()
        for module, name in modules:
            if module == self._views["module"]:
                menu.setActiveItem(name)
            else:
                menu.setInactiveItem(name, module)
        return str(menu)
