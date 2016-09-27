import __builtin__

try:
    from threading import local
except ImportError:
    from dummy_threading import local


class _cache(object):
    pass


class Request(local):
    def init(self, request):
        self.web = request
        self.user = None
        self.view = None
        self.menu = None
        self.dataset = None
        self.parameters = None
        self.cache = _cache()

    def __init__(self):
        local.__init__(self)
        self.init(None)


class Env:
    htdocs_mapping = {}
    request = Request()


env = Env()
__builtin__.env = env


# import after env creation
import localization
