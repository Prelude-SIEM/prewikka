from prewikka import PyTpl

class TopLayout(PyTpl.Template):
    def setSoftware(self, software):
        self.SOFTWARE = software

    def setPlace(self, place):
        self.PLACE = place

    def setTitle(self, title):
        self.TITLE = title

    def setContent(self, content):
        self.CONTENT = content
