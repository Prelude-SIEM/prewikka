class Log:
    def __init__(self):
        self._backends = [ ]

    def registerBackend(self, backend):
        self._backends.append(backend)

    def _applyOnBackends(self, handler, request):
        for backend in self._backends:
            getattr(backend, handler)(request)

    def invalidQuery(self, query):
        self._applyOnBackends("invalidQuery", query)



class LogBackend:
    def invalidQuery(self, query):
        pass
