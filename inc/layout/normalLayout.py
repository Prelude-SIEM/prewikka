#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 

from PyTpl import PyTpl
from genericLayout import genericLayout

class normalLayout(genericLayout):

    def __init__(self, views):
        self._views = views
        tpl = PyTpl("tpl/normalLayout.tpl")

        if "help" in self._views: 
            tpl["help"].HELP =self._views["help"]

        if "modules" in self._views and "module" in self._views:
            tpl.MENU = self._getMenu(self._views["modules"], self._views['sid'])

        if "module" in self._views and "pages" in self._views:
            tpl.TOPMENU = self._getPageMenu(self._views["pages"], self._views["active"], self._views["module"], self._views['sid'])

        if "main" in self._views: 
            tpl.PAGE = self._views["main"]
        
        if "software" in self._views: 
            tpl.SOFTWARE = self._views["software"]
        
        if "title" in self._views: 
            tpl.TITLE = self._views["title"]
        
        if "place" in self._views: 
            tpl.PLACE = self._views["place"]

        self._output = tpl.get()

    def getPage(self):
        return self._output

    def _getPageMenu(self, pages, active, module, sid):
        tpl = PyTpl("tpl/topmenu.tpl")
        tpl.SID = sid
        for page, name in pages:
            if page==active:
                tpl['menu']['active'].NAME = name
                tpl['menu']['active'].parse()
            else:
                tpl['menu']['inactive'].NAME = name
                tpl['menu']['inactive'].LINK = page
                tpl['menu']['inactive'].MODULE = module
                tpl['menu']['inactive'].SID = sid
                tpl['menu']['inactive'].parse()

            tpl['menu'].parse()
        return tpl.get()

    def _getMenu(self, modules, sid):
        tpl = PyTpl("tpl/menu.tpl")
        tpl.SID = sid
        for module, name in modules:
            if module == self._views["module"]:
                tpl['menu']['active'].NAME = name
                tpl['menu']['active'].parse()
            else:
                tpl['menu']['inactive'].NAME = name
                tpl['menu']['inactive'].MOD = module
                tpl['menu']['inactive'].SID = sid
                tpl['menu']['inactive'].parse()
            tpl['menu'].parse()
        return tpl.get()

