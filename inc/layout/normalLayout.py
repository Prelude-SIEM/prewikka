#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from genericLayout import genericLayout
from templates.layouts.normal import Normal, Menu, TopMenu

class normalLayout(genericLayout):

    def __init__(self, views):
        self._views = views
        normal = Normal.Normal()

        if "help" in views:
            normal.setHelp(views["help"])

        if "modules" in views and "module" in views:
            normal.setMenu(self._getMenu(views["modules"]))

        if "module" in views and "pages" in views:
            normal.setTopMenu(self._getPageMenu(views["pages"], views["active"], views["module"]))

        if "main" in views:
            normal.setPage(views["main"])
        
        if "software" in views:
            normal.setSoftware(views["software"])
        
        if "title" in views:
            normal.setTitle(views["title"])
        
        if "place" in views:
            normal.setPlace(views["place"])
            
        self._output = str(normal)

    def __str__(self):
        return self._output

    def _getPageMenu(self, pages, active, module):
        menu = TopMenu.TopMenu()
        for page, action in pages:
            if page == active:
                menu.setActiveItem(page)
            else:
                menu.setInactiveItem(page, module, action)
        
        return str(menu)

    def _getMenu(self, modules):
        menu = Menu.Menu()
        for module in modules:
            if module == self._views["module"]:
                menu.setActiveItem(module)
            else:
                menu.setInactiveItem(module, module)
        return str(menu)
