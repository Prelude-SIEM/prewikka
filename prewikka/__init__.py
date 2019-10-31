from __future__ import absolute_import, division, print_function, unicode_literals

import errno
import os
import stat
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


# Set default umask and create temporary directory
os.umask(0o027)


from prewikka import mainmenu, siteconfig, utils, view


try:
    os.mkdir(siteconfig.tmp_dir, 0o700)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise

    if not os.access(siteconfig.tmp_dir, os.R_OK | os.W_OK | os.X_OK):
        raise Exception("Prewikka temporary directory '%s' lack u+rwx permissions" % siteconfig.tmp_dir)

    if stat.S_IMODE(os.stat(siteconfig.tmp_dir).st_mode) & stat.S_IRWXO:
        raise Exception("Prewikka temporary directory '%s' is world accessible" % siteconfig.tmp_dir)


class _cache(object):
    pass


class Request(local):
    def __init__(self):
        local.__init__(self)
        self._init(None)

    def _init(self, request):
        self.web = request
        self.user = None
        self.view = None
        self.has_menu = False
        self.dataset = None
        self.parameters = None
        self.cache = _cache()
        self.view_kwargs = {}
        self._cleanup_list = []

    def register_cleanup(self, callable):
        self._cleanup_list.append(callable)

    def cleanup(self):
        for i in self._cleanup_list:
            i()

    @utils.request_memoize_property("menu")
    def menu(self):
        self.has_menu = True
        return mainmenu.TimePeriod(self.menu_parameters)

    @utils.request_memoize_property("menu_parameters")
    def menu_parameters(self):
        return view.GeneralParameters(self.view, self.web.arguments)

    def init(self, request):
        self._init(request)


class FakeRequest(Request):
    def _init(self, request):
        Request._init(self, request)
        self.parameters = view.Parameters(None)
        self._menu_parameters = FakeParameters(None)

    @property
    def menu_parameters(self):
        return self._menu_parameters


class FakeParameters(view.Parameters):
    def register(self):
        mainmenu._register_parameters(self)


class Env(object):
    htdocs_mapping = {}
    request = Request()


env = Env()
builtins.env = env

# import after env creation
from . import localization  # noqa: imported but unused
