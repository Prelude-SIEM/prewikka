import sys

import Config
import Prelude
import Request

class CoreRequest(Request.Request):
    def __init__(self, request=None):
        Request.Request.__init__(self)
        self.registerField("module", str, hidden=True)
        self.registerField("action", str, hidden=True)
        if request:
            self.module = request.module
            self.action = request.action



class Core:
    def __init__(self):
        self._content_modules = { }
        self._content_module_names = [ ]
        self._config = Config.Config()
        self._initModules()
        self._initPrelude()

    def _initModules(self):
        sys.path.append("inc/modules")
        names = [ "mod_alert", "mod_test" ]
        for name in names:
            module = __import__(name)
            module.load(self, self._config.modules.get(name, { }))

    def _initPrelude(self):
        self.prelude = Prelude.Prelude(self._config["prelude"])

    def registerContentModule(self, module):
        name = module.getName()
        self._content_module_names.append(name)
        self._content_modules[name] = module

    def getContentModuleNames(self):
        return self._content_module_names
        
    def process(self, request, response):
        module_name = request.get("module", "Alerts")
        module = self._content_modules[module_name]
        interface = module.process(self._config["interface"], request)
        response.write(interface)
        
