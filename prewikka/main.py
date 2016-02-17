# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
#
# This file is part of the Prewikka program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import pkg_resources
from prewikka import siteconfig, template
import os
import prelude
import preludedb
import json
import mimetypes

try:
    from threading import Lock, local
except ImportError:
    from dummy_threading import Lock, local


from prewikka import view, config, log, database, idmefdatabase, version, \
                     auth, error, utils, localization, resolve, theme, \
                     pluginmanager, renderer, env, dataprovider, menu
from prewikka.myconfigparser import ConfigParserSection

from prewikka.templates import ClassicLayout


_ADDITIONAL_MIME_TYPES = [("application/vnd.oasis.opendocument.formula-template", ".otf"),
                          ("application/vnd.ms-fontobject", ".eot"),
                          ("image/vnd.microsoft.icon", ".ico"),
                          ("application/font-woff", ".woff"),
                          ("application/font-sfnt", ".ttf"),
                          ("application/json", ".map"),
                          ("font/woff2", ".woff2")]

for mtype, extension in _ADDITIONAL_MIME_TYPES:
    mimetypes.add_type(mtype, extension)


class Logout(view._View):
    view_parameters = view.Parameters
    view_permissions = []

    def render(self):
        env.session.logout(self.request)


class BaseView(view._View):
    view_template = ClassicLayout.ClassicLayout

    def render(self):
        self._render(self.dataset, self.request, self.user)

    def _render(self, dataset, request, user):
        interface = env.config.interface

        # The database attribute might be None in case of initialisation error
        # FIXME: move me to a plugin !
        try:
            theme_name = user.get_property("theme", default=env.config.default_theme)
        except:
            theme_name = env.config.default_theme

        dataset["document.title"] = interface.getOptionValue("browser_title", "Prelude OSS")

        dataset["document.css_files"] = ["prewikka/css/jquery-ui.min.css",
                                         "prewikka/css/bootstrap.min.css",
                                         "prewikka/css/jquery.jstree.css",
                                         "prewikka/css/jquery-ui-timepicker-addon.min.css",
                                         "prewikka/css/font-awesome.min.css",
                                         "prewikka/css/ui.jqgrid.min.css",
                                         "prewikka/css/ui.multiselect.css",
                                         "prewikka/css/loader.css",
                                         "prewikka/css/themes/%s.css" % theme_name]

        dataset["document.js_files"] = ["prewikka/js/jquery.js",
                                        "prewikka/js/jquery-ui.min.js",
                                        "prewikka/js/bootstrap.min.js",
                                        "prewikka/js/functions.js",
                                        "prewikka/js/ajax.js",
                                        "prewikka/js/underscore-min.js",
                                        "prewikka/js/jquery-ui-timepicker-addon.min.js",
                                        "prewikka/js/ui.multiselect.js",
                                        "prewikka/js/jquery.jqgrid.min.js",
                                        "prewikka/js/commonlisting.js",
                                        "prewikka/js/jquery.jstree.js"]

        for type_ in ("css", "js"):
            for i in env.hookmgr.trigger("HOOK_LOAD_HEAD_CONTENT_%s" % type_.upper()):
                l = dataset["document.%s_files" % type_]
                l += (href for href in i if href not in l)

        dataset["prewikka.favicon"] = interface.getOptionValue(
            "favicon",
            "prewikka/images/favicon.ico"
        )
        dataset["prewikka.software"] = interface.getOptionValue(
            "software",
            "<img src='prewikka/images/prelude-logo.png' alt='Prelude' />"
        )

        dataset["prewikka.date"] = localization.format_date()
        if user:
            if interface.getOptionValue("user_display") == "name":
                dataset["prewikka.user_display"] = user.get_property("fullname", default=user.name)
            else:
                dataset["prewikka.user_display"] = user.name

        dataset["prewikka.logout_link"] = (user and env.session.can_logout()) and utils.create_link("logout") or None

        try:
            paths = request.getViewElements()
            active_section, active_tab = paths[0], paths[1]
        except:
            active_section, active_tab = "", ""

        dataset["interface.active_tab"] = active_tab
        dataset["interface.active_section"] = active_section
        dataset["interface.sections"] = env.menumanager.get_sections(user) if env.menumanager else {}
        dataset["interface.menu"] = env.menumanager.get_menus(user) if env.menumanager else {}
        dataset["toplayout_extra_content"] = ""

        all(env.hookmgr.trigger("HOOK_TOPLAYOUT_EXTRA_CONTENT",
                                request, user, dataset))
_core_cache = {}
_core_cache_lock = Lock()


def get_core_from_config(path, threaded=False):
    global _core_cache
    global _core_cache_lock

    if not path:
        path = siteconfig.conf_dir + "/prewikka.conf"

    with _core_cache_lock:
        if not path in _core_cache:
            _core_cache[path] = Core(path)

    return _core_cache[path]


class Core:
    def _checkVersion(self):
        error_type = _("Version Requirement error")
        if not prelude.checkVersion(siteconfig.libprelude_required_version):
            raise error.PrewikkaUserError(error_type, _("Prewikka %(vPre)s requires libprelude %(vLib)s or higher") % {'vPre':version.__version__, 'vLib':siteconfig.libprelude_required_version})

        elif not preludedb.checkVersion(siteconfig.libpreludedb_required_version):
            raise error.PrewikkaUserError(error_type, _("Prewikka %(vPre)s requires libpreludedb %(vLib)s or higher") % {'vPre':version.__version__, 'vLib':siteconfig.libpreludedb_required_version})

    def __init__(self, filename=None):
        env.auth = None # In case of database error
        env.config = config.Config(filename)

        env.config.default_theme = env.config.general.getOptionValue("default_theme", "cs")
        env.config.default_locale = env.config.general.getOptionValue("default_locale", "en_GB")
        env.config.default_timezone = env.config.general.getOptionValue("default_timezone", localization.get_system_timezone())
        env.config.default_encoding = env.config.general.getOptionValue("encoding", "UTF-8")

        env.log = log.Log(env.config)
        env.log.info("Starting Prewikka")

        env.hookmgr = pluginmanager.PluginHookManager()
        env.hookmgr.declare("HOOK_TOPLAYOUT_EXTRA_CONTENT")
        env.hookmgr.declare("HOOK_PROCESS_REQUEST")
        env.hookmgr.declare("HOOK_LINK")
        env.hookmgr.declare("HOOK_LOAD_HEAD_CONTENT_CSS", list)
        env.hookmgr.declare("HOOK_LOAD_HEAD_CONTENT_JS", list)

        env.dns_max_delay = float(env.config.general.getOptionValue("dns_max_delay", 0))

        val = env.config.general.getOptionValue("external_link_new_window", "true")
        if val is None or val.lower() in ["true", "yes"]:
            env.external_link_target = "_blank"
        else:
            env.external_link_target = "_self"

        # Get prewikka.conf option "enable_flags" and store it into environment
        flags = env.config.general.getOptionValue("enable_flags", "true")
        env.enable_flags = flags is None or flags.lower() in ["true", "yes"]

        details = env.config.general.getOptionValue("enable_details", "false")
        env.enable_details = details is None or details.lower() in ["true", "yes"]

        env.host_details_url = env.config.general.getOptionValue("host_details_url", "https://www.prelude-siem.com/host_details.php")
        env.port_details_url = env.config.general.getOptionValue("port_details_url", "https://www.prelude-siem.com/port_details.php")
        env.reference_details_url = env.config.general.getOptionValue("reference_details_url", "https://www.prelude-siem.com/reference_details.php")

        resolve.init()

        env.viewmanager = None
        env.menumanager = None
        env.htdocs_mapping.update((("prewikka", pkg_resources.resource_filename(__name__, 'htdocs')),))

        custom_theme = env.config.interface.getOptionValue("custom_theme", None)
        if custom_theme:
            if os.path.isdir("%s%s" % (os.path.sep, custom_theme)):
                env.htdocs_mapping.update((("custom", custom_theme),))
            else:
                env.htdocs_mapping.update((("custom", pkg_resources.resource_filename(custom_theme, 'htdocs')),))

        try:
            self._prewikka_initialized = False
            self._prewikka_init_if_needed()
        except:
            pass

    def _prewikka_init_if_needed(self):
        if self._prewikka_initialized is True:
            return self._reload_plugin_if_needed()

        try:
            self._checkVersion()
            env.db = database.Database(env.config.database)
            env.idmef_db = idmefdatabase.IDMEFDatabase(env.config.idmef_database)
            self._initURL()
            self._loadPlugins()
            self._prewikka_initialized = True
        except error.PrewikkaUserError, e:
            self._prewikka_initialized = e
        except (database.DatabaseSchemaError, preludedb.PreludeDBError), e:
            self._prewikka_initialized = error.PrewikkaUserError(_("Database error"), e)
        except Exception, e:
            self._prewikka_initialized = error.PrewikkaUserError(_("Initialization error"), e)

        if isinstance(self._prewikka_initialized, Exception):
            env.log.log(self._prewikka_initialized.log_priority, str(self._prewikka_initialized))
            raise self._prewikka_initialized

    def _initURL(self):
        env.url = {}
        for urltype in env.config.url:
            env.url[urltype] = {}
            for option in env.config.url[urltype].getOptions():
                env.url[urltype][option.name] = option.value

    def _load_auth_or_session(self, typename, plugins, name, config=None):
        if name not in plugins:
            raise error.PrewikkaUserError(
                "Initialization error",
                "Cannot use %(type)s mode '%(name)s', please contact your local administrator." %
                {'type': typename, 'name': name}
            )

        if config:
            config = config.getSection(name)
        else:
            config = ConfigParserSection(name)

        obj = plugins[name](config)
        setattr(env, typename, obj)
        obj.init(config)

    def _loadPlugins(self, last_change=None):
        env.menumanager = menu.MenuManager()
        env.dataprovider = dataprovider.DataProviderManager()
        env.viewmanager = view.ViewManager()

        env.plugins = {}
        for i in pluginmanager.PluginManager("prewikka.plugins"):
            try:
                env.plugins[i.__name__] = i()
            except error.PrewikkaUserError as err:
                env.log.warning("%s: plugin loading failed: %s" % (i.__name__, err))

        # Load views before auth/session to find all permissions
        env.viewmanager.loadViews()

        _AUTH_PLUGINS = pluginmanager.PluginManager("prewikka.auth", autoupdate=True)
        _SESSION_PLUGINS = pluginmanager.PluginManager("prewikka.session", autoupdate=True)
        cfg = env.config

        if cfg.session:
            self._load_auth_or_session("session", _SESSION_PLUGINS, cfg.session.name, cfg.session)
            if isinstance(env.session, auth.Auth):
                # If the session module is also an auth module, no need to load an auth module
                env.auth = env.session
                if cfg.auth:
                    env.log.error(_("Session '%s' does not accept any authentication module" % cfg.session.name))
            else:
                # If no authentification module defined, we use the session's default auth module
                auth_name = cfg.auth.name if cfg.auth else env.session.get_default_auth()
                self._load_auth_or_session("auth", _AUTH_PLUGINS, auth_name, cfg.auth)
        elif cfg.auth:
            # No session module defined, we load the auth module first
            self._load_auth_or_session("auth", _AUTH_PLUGINS, cfg.auth.name, cfg.auth)
            self._load_auth_or_session("session", _SESSION_PLUGINS, env.auth.getDefaultSession())
        else:
            # Nothing defined, we use the anonymous module
            self._load_auth_or_session("session", _SESSION_PLUGINS, "anonymous")
            env.auth = env.session

        env.viewmanager.addView(BaseView())
        if env.session.can_logout():
                env.viewmanager.addView(Logout())

        env.renderer = renderer.RendererPluginManager()

        self._last_plugin_activation_change = last_change or env.db.get_last_plugin_activation_change()

    def _setupDataSet(self, dataset, request, user):
        login = user.name if user else None

        dataset["document.base_url"] = request.getBaseURL()
        dataset["document.fullhref"] = "/".join(request.getViewElements()) # Needed for view that aren't completly ported to ajax
        dataset["document.href"] = "/".join(request.getViewElements()[0:2]) # Subview are hidden
        dataset["document.request_method"] = request.getMethod()
        dataset["document.query_string"] = request.getQueryString()
        dataset["document.charset"] = localization.getCurrentCharset()
        dataset["toplayout_extra_content"] = ""
        dataset["prewikka.user"] = user
        dataset["prewikka.about"] = utils.create_link("About")

    def handleError(self, request, err, user):
        dataset, template_name = None, None

        if not isinstance(err, error.PrewikkaUserError):
            err = error.PrewikkaUserError(_("Prelude internal error"), err, display_traceback=True)

        login = user.name if user else err.log_user
        if str(err):
                env.log.log(err.log_priority, err, request=request, user=login)

        if request.is_stream or request.is_xhr:
            request.content = json.dumps({"name": err.name, "message": err.message, "code": err.code, "traceback": err.traceback})
            if request.is_stream:
                request.sendStream(request.content, event="error")
                request.content = None

        else:
            # This case should only occur in case of auth error (and viewmgr might not exist at this time)
            dataset = err.setupDataset()
            v = BaseView()
            v._render(dataset, request, user)
            self._setupDataSet(dataset, request, user)

        return dataset

    def _reload_plugin_if_needed(self):
        last = env.db.get_last_plugin_activation_change()
        if last <= self._last_plugin_activation_change:
            return

        # Some changes happened, and every process has to reload the plugin configuration
        env.log.warning("plugins were activated: triggering reload (hook warning may follow)")

        env.hookmgr.unregister()
        self._loadPlugins(last_change=last)

    def process(self, request):
        user = None
        http_rcode = 200
        view_object = None

        encoding = env.config.general.getOptionValue("encoding", "utf8")
        try:
            self._prewikka_init_if_needed()

            env.threadlocal.user = user = env.session.get_user(request)
            user.set_locale()

            if not all(env.hookmgr.trigger("HOOK_PROCESS_REQUEST", request, user)):
                return

            if not request.path or request.path == "/":
                default_view = env.config.general.getOptionValue("default_view", "alerts/alerts")
                if not env.viewmanager.getViewIDFromPaths(default_view.split('/')):
                    # The configured view does not exist. Fall back to "settings/my_account"
                    # which does not require any specific permission.
                    default_view = "settings/my_account"
                raise error.RedirectionError("%s%s" % (request.getBaseURL(), default_view), 302)

            view_object = env.viewmanager.loadView(request, user)
            if view_object.dataset is not None:
                self._setupDataSet(view_object.dataset, request, user)

            resolve.process(env.dns_max_delay)
            request.content = view_object.respond()

        except error.RedirectionError as err:
            return request.sendRedirect(err.location, err.code)

        except Exception, err:
            http_rcode = getattr(err, "code", 500)

            dataset = self.handleError(request, err, user)
            if dataset:
                request.content = dataset.render()

        if request.content and request.force_download != True:
            request.content = request.content.encode(encoding, "xmlcharrefreplace")

        request.sendResponse(http_rcode)
