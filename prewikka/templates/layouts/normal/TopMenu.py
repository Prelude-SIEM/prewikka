from prewikka import PyTpl


class TopMenu(PyTpl.Template):
    def setActiveItem(self, name):
        self["menu"]["active"].NAME = name
        self["menu"]["active"].parse()
        self["menu"].parse()

    def setInactiveItem(self, name, link):
        self["menu"]["inactive"].NAME = name
        self["menu"]["inactive"].LINK = link
        self["menu"]["inactive"].parse()
        self["menu"].parse()
