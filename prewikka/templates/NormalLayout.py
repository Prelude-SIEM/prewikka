import sys

from prewikka import PyTpl

class NormalLayout(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self._tab_entries = [ ]
        self._menu_entries = [ ]
        self._special_actions = [ ]
        self._content = ""

    def addInactiveTabEntry(self, name, link):
        self._tab_entries.append({ "type": "inactive", "name": name, "link": link })
        
    def addActiveTabEntry(self, name, link):
        self._tab_entries.append({ "type": "active", "name": name, "link": link })

    def addInactiveMenuEntry(self, name, link):
        self._menu_entries.append({ "type": "inactive", "name": name, "link": link })
        
    def addActiveMenuEntry(self, name):
        self._menu_entries.append({ "type": "active", "name": name })
        
    def addSpecialAction(self, name, link):
        self._special_actions.append((name, link))
        
    def setContent(self, content):
        self._content = content
        
    def __str__(self):
        for entry in self._tab_entries:
            type = entry["type"]
            self["tab_entry"][type].NAME = entry["name"]
            self["tab_entry"][type].LINK = entry["link"]
            self["tab_entry"][type].parse()
            self["tab_entry"].parse()

        for name, link in self._special_actions:
            self["special"].LINK = link
            self["special"].NAME = name
            self["special"].parse()
            
        for entry in self._menu_entries:
            type = entry["type"]
            self["menu_entry"][type].NAME = entry["name"]
            if type == "inactive":
                self["menu_entry"][type].LINK = entry["link"]
            self["menu_entry"][type].parse()
            self["menu_entry"].parse()

        self.CONTENT = self._content

        return PyTpl.Template.__str__(self)
