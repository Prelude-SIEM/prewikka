import PyTpl

class Menu(PyTpl.Template):
    def __init__(self):
        PyTpl.PyTpl.__init__(self, "tpl/menu.tpl")

    def setActiveItem(self, name):
        self["menu"]["active"].NAME = name
        self["menu"]["active"].parse()

    def setInactiveItem(self, name, module):
        self["menu"]["inactive"].NAME = name
        self["menu"]["inactive"].MOD = module
        self["menu"]["inactive"].parse()
