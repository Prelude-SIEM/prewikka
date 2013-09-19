# Copyright (C) 2004-2012 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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

import os, copy, time
import prelude, preludedb, CheetahFilters

import prewikka.views
from prewikka import view, Config, Log, Database, IDMEFDatabase, \
     User, Auth, DataSet, Error, utils, siteconfig, localization, resolve

try:
    from threading import Lock
except ImportError:
    from dummy_threading import Lock


class InvalidQueryError(Error.PrewikkaUserError):
    def __init__(self, message):
        Error.PrewikkaUserError.__init__(self, _("Invalid query"), message, log=Log.ERROR)


class Logout(view.View):
    view_name = "logout"
    view_parameters = view.Parameters
    view_permissions = [ ]

    def render(self):
        self.env.auth.logout(self.request)

def load_template(name, dataset):
    template = getattr(__import__("prewikka.templates." + name, globals(), locals(), [ name ]), name)(filtersLib=CheetahFilters)

    for key, value in dataset.items():
        setattr(template, key, value)

    return template


_core_cache = { }
_core_cache_lock = Lock()


def get_core_from_config(path, threaded=False):
    global _core_cache
    global _core_cache_lock

    if not path:
        path = siteconfig.conf_dir + "/prewikka.conf"

    if threaded:
        _core_cache_lock.acquire()

    if not _core_cache.has_key(path):
        _core_cache[path] = Core(path)

    if threaded:
        _core_cache_lock.release()

    return _core_cache[path]



class Core:
    def _checkVersion(self):
        self._prelude_version_error = None

        if not prelude.prelude_check_version(siteconfig.libprelude_required_version):
            self._prelude_version_error = _("Prewikka %(vPre)s requires libprelude %(vLib)s or higher") % {'vPre':siteconfig.version, 'vLib':siteconfig.libprelude_required_version}

        elif not preludedb.preludedb_check_version(siteconfig.libpreludedb_required_version):
            self._prelude_version_error = _("Prewikka %(vPre)s requires libpreludedb %(vLib)s or higher") % {'vPre':siteconfig.version, 'vLib':siteconfig.libpreludedb_required_version}

    def __init__(self, config=None):
        class Env: pass
        self._env = Env()
        self._env.auth = None # In case of database error
        self._env.config = Config.Config(config)
        self._env.log = Log.Log(self._env.config)
        self._env.dns_max_delay = float(self._env.config.general.getOptionValue("dns_max_delay", 0))
        self._env.max_aggregated_source = int(self._env.config.general.getOptionValue("max_aggregated_source", 10))
        self._env.max_aggregated_target = int(self._env.config.general.getOptionValue("max_aggregated_target", 10))
        self._env.default_locale = self._env.config.general.getOptionValue("default_locale", None)

	val = self._env.config.general.getOptionValue("external_link_new_window", "true")
        if val.lower() in ["true", "yes"]:
            self._env.external_link_target = "_blank"
        else:
            self._env.external_link_target = "_self"

        val = self._env.config.general.getOptionValue("enable_details", "false")
        if val.lower() in ["true", "yes"]:
            self._env.enable_details = True
        else:
            self._env.enable_details = False

        self._env.host_details_url = self._env.config.general.getOptionValue("host_details_url", "https://www.prelude-ids.com/host_details.php")
        self._env.port_details_url = self._env.config.general.getOptionValue("port_details_url", "https://www.prelude-ids.com/port_details.php")
        self._env.reference_details_url = self._env.config.general.getOptionValue("reference_details_url", "https://www.prelude-ids.com/reference_details.php")

        if self._env.dns_max_delay != -1:
            resolve.init(self._env)

        preludedb.preludedb_init()

        self._checkVersion()

        self._database_schema_error = None
        try:
            self._initDatabase()
        except Database.DatabaseSchemaError, e:
            self._database_schema_error = e

        self._env.idmef_db = IDMEFDatabase.IDMEFDatabase(self._env.config.idmef_database)
        self._initHostCommands()
        self._initURL()
        self._loadViews()
        self._loadModules()
        self._initAuth()


    def _initDatabase(self):
        config = { }
        for key in self._env.config.database.keys():
            config[key] = self._env.config.database.getOptionValue(key)

        self._env.db = Database.Database(config)

    def _initHostCommands(self):
        self._env.host_commands = { }

        for option in self._env.config.host_commands.getOptions():
            if os.access(option.value.split(" ")[0], os.X_OK):
                self._env.host_commands[option.name] = option.value

    def _initURL(self):
        self._env.url = {}
        for urltype in self._env.config.url:
            self._env.url[urltype] = {}
            for option in self._env.config.url[urltype].getOptions():
                self._env.url[urltype][option.name] = option.value

    def _initAuth(self):
        if self._env.auth.canLogout():
            self._views.update(Logout().get())

    def _loadViews(self):
        self._view_to_tab = { }
        self._view_to_section = { }

        for section, tabs in (prewikka.views.events_section, prewikka.views.agents_section, prewikka.views.stats_section,
                              prewikka.views.settings_section, prewikka.views.about_section):
            for tab, views in tabs:
                for view in views:
                    self._view_to_tab[view] = tab
                    self._view_to_section[view] = section

        self._views = { }
        for object in prewikka.views.objects:
            self._views.update(object.get())

    def _loadModule(self, type, name, config):
        module = __import__("prewikka.modules.%s.%s.%s" % (type, name, name), globals(), locals(), [ name ])
        return module.load(self._env, config)

    def _loadModules(self):
        config = self._env.config

        if config.auth:
            self._env.auth = self._loadModule("auth", config.auth.name, config.auth)
        else:
            self._env.auth = self._loadModule("auth", "anonymous", config.auth)

    def _setupView(self, view, request, parameters, user):
        object = view["object"]
        if not object.view_initialized:
            object.init(self._env)
            object.view_initialized = True

        object = copy.copy(object)

        object.request = request
        object.parameters = parameters
        object.user = user
        object.dataset = DataSet.DataSet()
        object.env = self._env

        return object

    def _cleanupView(self, view):
        del view.request
        del view.parameters
        del view.user
        del view.dataset
        del view.env

    def _init_dataset(self, dataset, request):
        interface = self._env.config.interface
    	dataset["document.title"] = "[PREWIKKA]"
    	dataset["document.charset"] = localization.getCurrentCharset()
    	dataset["document.css_files"] = [ "/prewikka/css/style.css" ]
    	dataset["document.js_files"] = [ "/prewikka/js/jquery.js", "/prewikka/js/functions.js" ]
    	dataset["prewikka.title"] = interface.getOptionValue("title", "&nbsp;")
    	dataset["prewikka.software"] = interface.getOptionValue("software", "&nbsp;")
    	dataset["prewikka.place"] = interface.getOptionValue("place", "&nbsp;")
    	dataset["prewikka.date"] = localization.getDate()
        dataset["prewikka.external_link_target"] = self._env.external_link_target
        dataset["prewikka.enable_details"] = self._env.enable_details
        dataset["prewikka.host_details_url"] = self._env.host_details_url
        dataset["prewikka.port_details_url"] = self._env.port_details_url
        dataset["prewikka.reference_details_url"] = self._env.reference_details_url

	dataset["arguments"] = []
        for name, value in request.arguments.items():
            if name in ("_login", "_password"):
                continue

            if name == "view" and value == "logout":
                continue

            dataset["arguments"].append((name, utils.toUnicode(value)))

        return dataset

    def _setupDataSet(self, dataset, request, user, view=None, parameters={}):
        dataset = self._init_dataset(dataset, request)

        sections = prewikka.views.events_section, prewikka.views.agents_section, prewikka.views.stats_section, prewikka.views.settings_section, \
                   prewikka.views.about_section

        section_to_tabs = { }
        dataset["interface.sections"] = [ ]
        for section_name, tabs in sections:
            first_tab = None

            for tab_name, views in tabs:
                view_name = views[0]

                if not user or user.has(self._views[view_name]["permissions"]):
                    if not first_tab:
                        first_tab = view_name
                        section_to_tabs[section_name] = []

                    section_to_tabs[section_name] += [ ((tab_name, utils.create_link(views[0]))) ]

            if first_tab:
                dataset["interface.sections"].append( (section_name, utils.create_link(first_tab)) )


        if isinstance(parameters, prewikka.view.RelativeViewParameters) and parameters.has_key("origin"):
            view_name = parameters["origin"]
        elif view:
            view_name = view["name"]
        else:
            view_name = None

        if view_name and self._view_to_section.has_key(view_name):
            active_section = self._view_to_section[view_name]
            active_tab = self._view_to_tab[view_name]
            tabs = section_to_tabs.get(active_section, [])

        else:
            active_section, tabs, active_tab = "", [ ], ""

        dataset["interface.tabs"] = tabs
        dataset["prewikka.user"] = user

        if user:
            dataset["prewikka.userlink"] = "<b><a href=\"%s\">%s</a></b>" % (utils.create_link("user_settings_display"), utils.escape_html_string(user.login))

        dataset["interface.active_tab"] = active_tab
        dataset["interface.active_section"] = active_section
        dataset["prewikka.logout_link"] = (user and self._env.auth.canLogout()) and utils.create_link("logout") or None

    def _printDataSet(self, dataset, level=0):
        for key, value in dataset.items():
            print " " * level * 8,
            if isinstance(value, DataSet.DataSet):
                print key + ":"
                self._printDataSet(value, level + 1)
            else:
                print "%s: %s" % (key, repr(value))

    def _checkPermissions(self, request, view, user):
        if user and view.has_key("permissions"):
            if not user.has(view["permissions"]):
                raise User.PermissionDeniedError(view["name"])

    def _getParameters(self, request, view, user):
        parameters = view["parameters"](request.arguments) - [ "view" ]
        parameters.add_params(self._env.idmef_db)
        parameters.normalize(view["name"], user)

        return parameters

    def _getView(self, request, user):
        name = request.getView()
        try:
            return self._views[name]

        except KeyError:
            raise InvalidQueryError(_("View '%s' does not exist") % name)

    def checkAuth(self, request):
        user = self._env.auth.getUser(request)
        if not user.language and self._env.default_locale:
            user.setLanguage(self._env.default_locale)

        return user

    def prepareError(self, e, request, user, login, view):
        e = unicode(repr(e))
        self._env.log.error(e, request, login)
        error = Error.PrewikkaUserError(_("Prewikka internal error"), e,
                                        display_traceback=not self._env.config.general.has_key("disable_error_traceback"))
        self._setupDataSet(error.dataset, request, user, view=view)
        return error

    def process(self, request):
        login = None
        view = None
        user = None
        encoding = self._env.config.general.getOptionValue("encoding", "utf8")

        try:
            if self._prelude_version_error:
                raise Error.PrewikkaUserError(_("Version Requirement error"), self._prelude_version_error)

            if self._database_schema_error != None:
                raise Error.PrewikkaUserError(_("Database error"), self._database_schema_error)

            user = self.checkAuth(request)
            login = user.login
            view = self._getView(request, user)

            self._checkPermissions(request, view, user)
            parameters = self._getParameters(request, view, user)
            view_object = self._setupView(view, request, parameters, user)

            if not isinstance(view_object, Logout):
                self._env.log.info("Loading view", request, user.login)

            getattr(view_object, view["handler"])()
            self._setupDataSet(view_object.dataset, request, user, view, parameters)

            dataset = view_object.dataset
            template_name = view["template"]

            self._cleanupView(view_object)

        except Error.PrewikkaUserError, e:
            if e._log_priority:
                self._env.log.log(e._log_priority, unicode(e), request=request, user=login or e._log_user)

            self._setupDataSet(e.dataset, request, user, view=view)
            dataset, template_name = e.dataset, e.template

        except Exception, e:
            error = self.prepareError(e, request, user, login, view)
            dataset, template_name = error.dataset, error.template

        #self._printDataSet(dataset)
        template = load_template(template_name, dataset)

        # We check the character set after loading the template,
        # since the template might trigger a language change.
        dataset["document.charset"] = localization.getCurrentCharset()
        resolve.process(self._env.dns_max_delay)

        try:
                request.content = template.respond()
        except Exception, e:
            error = self.prepareError(e, request, user, login, view)
            request.content = load_template(error.template, error.dataset).respond()

        request.content = request.content.encode(encoding, "xmlcharrefreplace")
        request.sendResponse()

