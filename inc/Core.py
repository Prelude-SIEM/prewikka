import sys
import os, os.path

import Config
import Log
import Prelude
import Interface

class Core:
    def __init__(self):
        self.content_modules = { }
        self._content_module_names = [ ]
        self._config = Config.Config()
        self.interface = Interface.Interface(self, self._config.get("interface", { }))
        self.log = Log.Log()
        self.prelude = Prelude.Prelude(self._config["prelude"])
        self._initModules()

    def _initModules(self):
        sys.path.append(".")
        base_dir = "inc/modules/"
        files = os.listdir(base_dir)
        for file in files:
            if os.path.isdir(base_dir + file):
                name = os.path.basename(file)
                if os.path.isfile(base_dir + file + "/" + name + ".py"):
                    module = __import__(base_dir + file + "/" + name)
                    module.load(self, self._config.modules.get(name, {}))
        
    def process(self, query, response):
        if query.has_key("action"):
            action = query["action"]
            del query["action"]
        else:
            action = None
        
        view = self.interface.process(action, query)
        response.write(view)
