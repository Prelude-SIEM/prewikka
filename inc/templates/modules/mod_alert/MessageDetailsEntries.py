import PyTpl

class AlertDetailsEntries(PyTpl.Template):
    def newEntry(self, name, value):
        self["entry"]["normal"].NAME = name
        self["entry"]["normal"].VALUE = value
        self["entry"]["normal"].parse()
        self["entry"].parse()

    def newSection(self, content):
        self["entry"]["section"].CONTENT = content
        self["entry"]["section"].parse()
        self["entry"].parse()
