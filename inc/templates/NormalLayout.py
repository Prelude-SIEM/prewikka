import PyTpl

class NormalLayout(PyTpl.Template):
    def __init__(self):
        PyTpl.PyTpl.__init__(self, "tpl/normalLayout.tpl")

    def setHelp(self, help):
        self["help"].HELP = help

    def setMenu(self, menu):
        self.MENU = menu

    def setTopMenu(self, top_menu):
        self.TOPMENU = top_menu

    def setPage(self, page):
        self.PAGE = page

    def setSoftware(self, software):
        self.SOFTWARE = software

    def setTitle(self, title):
        self.TITLE = title

    def setPlace(self, place):
        self.PLACE = place
