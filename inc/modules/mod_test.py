import sys
from PyTpl import PyTpl

class Form(PyTpl):
    def __init__(self):
        PyTpl.__init__(self, "tpl/form.tpl")

    def setFixedField(self, key, value):
        self["fixed"].KEY = key
        self["fixed"].VALUE = value
        self["fixed"].parse()

    def setInteractiveField(self, key, name):
        self["interactive"].NAME = name
        self["interactive"].KEY = key
        self["interactive"].parse()


class Display:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        ret = ""
        ret += "<p>foo: %s</p>\n" % self.query["foo"]
        ret += "<p>bar: %s</p>\n" % self.query["bar"]
        return ret


class Fetch:
    def __init__(self, query):
        self.query = query

    def __str__(self):
        form = Form()
        form.setFixedField("mod", "test")
        form.setFixedField("section", "display")
        form.setInteractiveField("display.foo", "foo")
        form.setInteractiveField("display.bar", "bar")
        ret = str(form)
        sys.stderr.write(">>>" + ret + "\n")
        return ret



def load(module):
    module.setName("Test")
    module.registerSection("fetch", Fetch, default=True)
    module.registerSection("display", Display, visible=False)
