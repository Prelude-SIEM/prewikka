class Log:
    def __init__(self):
        self._modules = [ ]

    def registerModule(self, module):
        self._modules.append(module)

    def _applyOnModules(self, handler, request):
        for module in self._modules:
            getattr(module, handler)(request)

    def invalidQuery(self, query):
        self._applyOnModules("invalidQuery", query)
