import sys
import glob
from layout import layoutManager
import config
from Module import Module
from Query import Query

class Frontend:
    def __init__(self):
        self.modules = { }
        self.module_names = [ ]
        self.__loadModules()
        
    def __loadModules(self):
        for mod_name in "mod_alert", "mod_test":
            self.module_names.append(mod_name)
            self.modules[mod_name] = Module(mod_name)
    
    def build(self, query):
        try:
            modname = query["mod"]
        except KeyError:
            modname = "alert"

        mod = self.modules["mod_" + modname]
        views = mod.build(query)
        
        if "headers" not in views:
            views['headers'] = ["Content-Type: text/html"]
        
        views['views']['modules'] = config.config['modules']
        views['views']['module'] = modname
        views['views']["software"] = config.config['software']
        views['views']['place'] = config.config['company']
        views['views']['title'] = config.config['title']
        views['views']['sid'] = ""
        
        layout = layoutManager.getLayout(views['layout'], views['views'], query)

        return "\n".join(views['headers']) + "\n\n" + str(layout)
