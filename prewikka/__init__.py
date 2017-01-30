from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import prelude
import preludedb

if sys.version_info >= (3, 0):
    import builtins
    builtins.text_type = str
else:
    import __builtin__ as builtins
    builtins.text_type = unicode

    prelude.python2_return_unicode(True)
    preludedb.python2_return_unicode(True)

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
        self.view_kwargs = {}

        # env.viewmanager might be empty in case of early error (database)
        if request and env.viewmanager:
            env.viewmanager.set_url_adapter(self)

    def __init__(self):
        local.__init__(self)
        self.init(None)


class Env:
    htdocs_mapping = {}
    request = Request()


env = Env()
builtins.env = env

# import after env creation
from . import localization
