import Interface
import Request

class Module:
    def __init__(self):
        self._name = None

    def setName(self, name):
        self._name = name

    def getName(self):
        return self._name



class ContentModule(Module):
    def __init__(self, core):
        Module.__init__(self)
        self._core = core
        self._sections = [ ]
        self._actions = { }
        self._default_action = None
    
    def registerAction(self, action, request, default=False):
        self._actions[action] = request
        if default:
            self._default_action = { "name": action, "request": request }
        
    def addSection(self, name, action):
        self._sections.append((name, action))

    def getSections(self):
        return self._sections
    
    def process(self, interface_config, query):
        if query.has_key("action"):
            action = query["action"]
            request_class = self._actions[action]
        else:
            action = self._default_action["name"]
            request_class = self._default_action["request"]
            
        handler = getattr(self, "handle_" + action)
        request = request_class()
        try:
            request.populate(query)
        except Request.Error:
            self._core.log.invalidQuery(query)
            interface_class = Interface.ErrorInterface
            data = "Query error"
        else:
            interface_class, data = handler(request)
        interface = interface_class(self._core, interface_config, request, data)
        interface.init()
        interface.build()

        return str(interface)



class LogModule(Module):
    def invalidQuery(self, query):
        pass
