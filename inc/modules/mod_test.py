import sys
from templates.modules.mod_test import Form
from templates import Table
import module
import interface
import core
import Request


class ModuleInterface(interface.NormalInterface):
    def init(self):
        interface.NormalInterface.init(self)
        self.setModuleName("Test")
        self.setTabs([ ("fetch", "fetch_data"), ("empty", "empty"), ("third", "third") ])



class DataInterface(ModuleInterface):
    def init(self):
        ModuleInterface.init(self)
        self.setActiveTab("fetch")



class EmptyInterface(ModuleInterface):
    def init(self):
        ModuleInterface.init(self)
        self.setActiveTab("empty")



class ThirdInterface(ModuleInterface):
    def init(self):
        ModuleInterface.init(self)
        self.setActiveTab("third")

    def build(self):
        table = Table.Table()
        table.setHeader(("Character", "Numeric"))
        for char, num in self._data:
            table.addRow((char, num))

        self.setMainContent(str(table))



class DisplayDataInterface(DataInterface):
    def build(self):
        foo, bar = self._data
        content = ""
        content += "<p>foo: %s</p>\n" % foo
        content += "<p>bar: %s</p>\n" % bar
        self.setMainContent(content)



class FetchDataInterface(DataInterface):
    def build(self):
        form = Form.Form()
        request = DataRequest()
        request.module = "Test"
        request.action = "display_data"
        for name in request.getHiddens():
            form.setFixedField(name, request[name])
        form.setInteractiveField("foo", "foo")
        form.setInteractiveField("bar", "bar")
        self.setMainContent(str(form))



class DataRequest(core.CoreRequest):
    def __init__(self):
        core.CoreRequest.__init__(self)
        self.registerField("foo", str)
        self.registerField("bar", str)



class TestModule(module.ContentModule):
    def __init__(self, _core):
        module.ContentModule.__init__(self, _core)
        self.setName("Test")
        self.registerAction("fetch_data", core.CoreRequest, default=True)
        self.registerAction("display_data", DataRequest)
        self.registerAction("empty", core.CoreRequest)
        self.registerAction("third", core.CoreRequest)

    def handle_fetch_data(self, request):
        return FetchDataInterface, None

    def handle_display_data(self, request):
        return DisplayDataInterface, (request["foo"], request["bar"])

    def handle_empty(self, request):
        return EmptyInterface, None

    def handle_third(self, request):
        return ThirdInterface, (("one", 1), ("two", 2), ("three", 3), ("four", 4))



def load(core, config):
    module = TestModule(core)
    core.registerContentModule(module)
