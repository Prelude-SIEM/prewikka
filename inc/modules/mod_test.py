import sys
from templates.modules.mod_test import Form
from templates import Table
import module
import Interface
import core
import Request


class TestInterface(Interface.NormalInterface):
    def init(self):
        Interface.NormalInterface.init(self)
        self.setActiveModule("Test")



class TestSection(TestInterface):
    def init(self):
        TestInterface.init(self)
        self.setActiveSection("Test")
        self.setTabs([ ("fetch", "fetch_data"), ("empty", "empty"), ("third", "third") ])

        

class DataView(TestSection):
    def init(self):
        TestSection.init(self)
        self.setActiveTab("fetch")



class DisplayDataViewInstance(DataView):
    def build(self):
        foo, bar = self._data
        content = ""
        content += "<p>foo: %s</p>\n" % foo
        content += "<p>bar: %s</p>\n" % bar
        self.setMainContent(content)



class FetchDataViewInstance(DataView):
    def build(self):
        form = Form.Form()
        request = DataRequest()
        request.setModule("Test")
        request.setAction("display_data")
        for name in request.keys(ignore=("foo", "bar")):
            form.setFixedField(name, request[name])
        form.setInteractiveField("foo", "foo")
        form.setInteractiveField("bar", "bar")
        self.setMainContent(str(form))



class EmptyView(TestSection):
    def init(self):
        TestSection.init(self)
        self.setActiveTab("empty")



class EmptyViewInstance(EmptyView):
    pass



class ThirdView(TestSection):
    def init(self):
        TestSection.init(self)
        self.setActiveTab("third")



class ThirdViewInstance(ThirdView):
    def build(self):
        table = Table.Table()
        table.setHeader(("Character", "Numeric"))
        for char, num in self._data:
            table.addRow((char, num))
        
        self.setMainContent(str(table))



class DataRequest(core.CoreRequest):
    def register(self):
        core.CoreRequest.register(self)
        self.registerField("foo", str)
        self.registerField("bar", str)

    def getFoo(self):
        return self.get("foo")

    def getBar(self):
        return self.get("bar")



class TestModule(module.ContentModule):
    def __init__(self, _core):
        module.ContentModule.__init__(self, _core)
        self.setName("Test")
        self.addSection("Test", "fetch_data")
        self.registerAction("fetch_data", core.CoreRequest, default=True)
        self.registerAction("display_data", DataRequest)
        self.registerAction("empty", core.CoreRequest)
        self.registerAction("third", core.CoreRequest)

    def handle_fetch_data(self, request):
        return FetchDataViewInstance, None

    def handle_display_data(self, request):
        return DisplayDataViewInstance, (request["foo"], request["bar"])

    def handle_empty(self, request):
        return EmptyViewInstance, None

    def handle_third(self, request):
        return ThirdViewInstance, (("one", 1), ("two", 2), ("three", 3), ("four", 4))



def load(core, config):
    module = TestModule(core)
    core.registerContentModule(module)
