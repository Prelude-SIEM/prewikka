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
import os
import prelude
import preludedb
import mimetypes

try:
    from threading import Lock, local
except ImportError:
    from dummy_threading import Lock, local


from prewikka import view, config, log, database, idmefdatabase, version, \
                     auth, error, localization, resolve, \
                     pluginmanager, renderer, env, dataprovider, menu, \
                     siteconfig, hookmanager, response

from prewikka.utils import viewhelpers


class Logout(view._View):
    view_parameters = view.Parameters
    view_permissions = []
    view_layout = None

    def render(self):
        env.session.logout(env.request.web)


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

        env.config.general.setdefault("default_theme", "cs")
        env.config.general.setdefault("default_locale", "en_GB")
        env.config.general.setdefault("encoding", "UTF-8")
        env.config.general.setdefault("default_timezone", localization.get_system_timezone())
        env.config.general.reverse_path = env.config.general.get("reverse_path", "").rstrip("/")

        env.log = log.Log(env.config)
        env.log.info("Starting Prewikka")

        env.dns_max_delay = float(env.config.general.get("dns_max_delay", 0))

        val = env.config.general.get("external_link_new_window", "true")
        if val is None or val.lower() in ["true", "yes"]:
            env.external_link_target = "_blank"
        else:
            env.external_link_target = "_self"

        details = env.config.general.get("enable_details", "false")
        env.enable_details = details is None or details.lower() in ["true", "yes"]

        env.host_details_url = env.config.general.get("host_details_url", "https://www.prelude-siem.com/host_details.php")
        env.port_details_url = env.config.general.get("port_details_url", "https://www.prelude-siem.com/port_details.php")
        env.reference_details_url = env.config.general.get("reference_details_url", "https://www.prelude-siem.com/reference_details.php")

        resolve.init()

        env.viewmanager = None
        env.menumanager = None
        env.htdocs_mapping.update((("prewikka", pkg_resources.resource_filename(__name__, 'htdocs')),))

        custom_theme = env.config.interface.get("custom_theme", None)
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
        for urlconf in env.config.url:
            env.url[urlconf.get_instance_name()] = {}
            for label, url in urlconf.items():
                env.url[urlconf.get_instance_name()][label] = url

    def _load_auth_or_session(self, typename, plugins, name, config=config.SectionRoot()):
        if name not in plugins:
            raise error.PrewikkaUserError(
                "Initialization error",
                "Cannot use %(type)s mode '%(name)s', please contact your local administrator." %
                {'type': typename, 'name': name}
            )

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
            self._load_auth_or_session("session", _SESSION_PLUGINS, cfg.session.get_instance_name(), cfg.session)
            if isinstance(env.session, auth.Auth):
                # If the session module is also an auth module, no need to load an auth module
                env.auth = env.session
                if cfg.auth:
                    env.log.error(_("Session '%s' does not accept any authentication module" % cfg.session.get_instance_name()))
            else:
                # If no authentification module defined, we use the session's default auth module
                auth_name = cfg.auth.get_instance_name() if cfg.auth else env.session.get_default_auth()
                self._load_auth_or_session("auth", _AUTH_PLUGINS, auth_name, cfg.auth)
        elif cfg.auth:
            # No session module defined, we load the auth module first
            self._load_auth_or_session("auth", _AUTH_PLUGINS, cfg.auth.get_instance_name(), cfg.auth)
            self._load_auth_or_session("session", _SESSION_PLUGINS, env.auth.getDefaultSession())
        else:
            # Nothing defined, we use the anonymous module
            self._load_auth_or_session("session", _SESSION_PLUGINS, "anonymous")
            env.auth = env.session

        env.viewmanager.addView(viewhelpers.AjaxHostURL())
        if env.session.can_logout():
                env.viewmanager.addView(Logout())

        env.renderer = renderer.RendererPluginManager()

        self._last_plugin_activation_change = last_change or env.db.get_last_plugin_activation_change()

    def _reload_plugin_if_needed(self):
        last = env.db.get_last_plugin_activation_change()
        if last <= self._last_plugin_activation_change:
            return

        # Some changes happened, and every process has to reload the plugin configuration
        env.log.warning("plugins were activated: triggering reload (hook warning may follow)")

        hookmanager.unregister()
        self._loadPlugins(last_change=last)

    def process(self, request):
        env.request.init(request)
        view_object = None

        encoding = env.config.general.get("encoding", "utf8")
        try:
            self._prewikka_init_if_needed()

            env.request.user = user = env.session.get_user(request)
            user.set_locale()

            if not all(hookmanager.trigger("HOOK_PROCESS_REQUEST", request, user)):
                return

            if not request.path or request.path == "/":
                default_view = env.config.general.get("default_view", "alerts/alerts")
                if not env.viewmanager.getViewIDFromPaths(default_view.split('/')):
                    # The configured view does not exist. Fall back to "settings/my_account"
                    # which does not require any specific permission.
                    default_view = "settings/my_account"
                raise error.RedirectionError("%s%s" % (request.getBaseURL(), default_view), 302)

            env.request.view = view_object = env.viewmanager.loadView(request, user)

            resolve.process(env.dns_max_delay)
            response = view_object.respond()

        except error.RedirectionError as err:
            return request.sendRedirect(err.location, err.code)

        except error.PrewikkaUserError as err:
            response = err.respond()

        except Exception, err:
            response = error.PrewikkaUserError(_("Prelude internal error"), err, display_traceback=True).respond()

        request.sendResponse(response)
