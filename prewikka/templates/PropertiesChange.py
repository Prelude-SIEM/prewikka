from prewikka import PyTpl


class PropertiesChange(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self.count = 0
    
    def addHiddenEntry(self, name, value):
        self["hidden"].NAME = name
        self["hidden"].VALUE = value
        self["hidden"].parse()
        
    def _addEntry(self, type, name, argument, value=""):
        self["entry"].TYPE = ("table_row_even", "table_row_odd")[self.count%2]
        self["entry"].NAME = name
        self["entry"]["value"][type].ARGUMENT = argument
        self["entry"]["value"][type].VALUE = value
        self["entry"]["value"][type].parse()
        self["entry"]["value"].parse()
        self["entry"].parse()
        self.count += 1
        
    def addTextEntry(self, name, argument, value=""):
        self._addEntry("text", name, argument, "value='%s'" % value)
        
    def addPasswordEntry(self, name, argument):
        self._addEntry("password", name, argument)
        
    def addCheckboxEntry(self, name, argument, checked=False):
        self._addEntry("checkbox", name, argument, ("", "checked")[checked])

    def setButtonLabel(self, label):
        self.BUTTON_LABEL = label
