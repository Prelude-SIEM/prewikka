import PyTpl

class TopMenu(PyTpl.Template):
    def setActiveItem(self, name):
        self["menu"]["active"].NAME = name
        self["menu"]["active"].parse()
        self["menu"].parse()

    def setInactiveItem(self, name, module, action):
        self["menu"]["inactive"].NAME = name
        self["menu"]["inactive"].MODULE = module
        self["menu"]["inactive"].ACTION = action
        self["menu"]["inactive"].parse()
        self["menu"].parse()
