import PyTpl

class Form(PyTpl.Template):
    def setFixedField(self, key, value):
        self["fixed"].KEY = key
        self["fixed"].VALUE = value
        self["fixed"].parse()

    def setInteractiveField(self, key, name):
        self["interactive"].NAME = name
        self["interactive"].KEY = key
        self["interactive"].parse()
