import PyTpl

class Menu(PyTpl.Template):
    def setActiveItem(self, name):
        self["menu"]["active"].NAME = name
        self["menu"]["active"].parse()
        self["menu"].parse()

    def setInactiveItem(self, name, module):
        self["menu"]["inactive"].NAME = name
        self["menu"]["inactive"].MOD = module
        self["menu"]["inactive"].parse()
        self["menu"].parse()
