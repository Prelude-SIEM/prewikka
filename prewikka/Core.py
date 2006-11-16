# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import sys
import time
import os, os.path
import distutils.spawn

import copy

import urllib
import cgi

import prelude, preludedb
import CheetahFilters

from prewikka import Config, Log, Database, IDMEFDatabase, ParametersNormalizer, \
     User, Auth, DataSet, Error, utils, siteconfig


class InvalidQueryError(Error.SimpleError):
    def __init__(self, query):
        Error.SimpleError.__init__(self, "query error", "invalid query")



class PermissionDeniedError(Error.SimpleError):
    def __init__(self, user, action_name):
        Error.SimpleError.__init__(self, "Permission Denied",
                                   "User %s cannot access action %s" % (user, action_name))



def init_dataset(dataset, config, request):
    interface = config.interface
    dataset["document.title"] = "[PREWIKKA]"
    dataset["document.css_files"] = [ "prewikka/css/style.css" ]
    dataset["document.js_files"] = [ "prewikka/js/functions.js" ]
    dataset["prewikka.title"] = interface.getOptionValue("title", "&nbsp;")
    dataset["prewikka.software"] = interface.getOptionValue("software", "&nbsp;")
    dataset["prewikka.place"] = interface.getOptionValue("place", "&nbsp;")
    dataset["prewikka.url.referer"] = cgi.parse_qs(urllib.splitquery(request.getReferer())[1] or "")
    dataset["prewikka.date"] = time.strftime("%A %B %d %Y")
    dataset["prewikka.query_string"] = utils.urlencode(request.arguments)
    
    val = config.general.getOptionValue("external_link_new_window", "true")
    if (not val and config.general.has_key("external_link_new_window")) or (val == None or val.lower() in ["true", "yes"]):
        dataset["prewikka.external_link_target"] = "_blank"
    else:
        dataset["prewikka.external_link_target"] = "_self"
            
    qstring = request.getQueryString()
    if qstring[0:2] == "/?":
        qstring = qstring[2:]

    dataset["prewikka.url.current"] = cgi.parse_qs(qstring)


def load_template(name, dataset):
    template = getattr(__import__("prewikka.templates." + name, globals(), locals(), [ name ]), name)(filtersLib=CheetahFilters)
        
    for key, value in dataset.items():
        setattr(template, key, value)

    return template


_core_cache = { }

try:
    import threading
except ImportError:
    _has_threads = False
else:
    _has_threads = True
    _core_cache_lock = threading.Lock()


def get_core_from_config(path, threaded=False):    
    global _core_cache

    if not path:
        path = siteconfig.conf_dir + "/prewikka.conf"

    if _has_threads and threaded:
        _core_cache_lock.acquire()
    
    if not _core_cache.has_key(path):
        _core_cache[path] = Core(path)

    if _has_threads and threaded:
        _core_cache_lock.release()
    
    return _core_cache[path]



class Core:
    def __init__(self, config=None):
        class Env: pass
        self._env = Env()
        self._env.config = Config.Config(config)
        preludedb.preludedb_init()
        self._initDatabase()
        self._env.idmef_db = IDMEFDatabase.IDMEFDatabase(self._env.config.idmef_database)
        self._env.log = Log.Log(self._env.config)
        self._initHostCommands()
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
        
    def _initAuth(self):
        if self._env.auth.canLogout():
            from prewikka import view

            class Logout(view.View):
                view_name = "logout"
                view_parameters = view.Parameters
                view_permissions = [ ]
                
                def render(self):
                    self.env.auth.logout(self.request)
            
            self._views.update(Logout().get())

    def _loadViews(self):
        import prewikka.views
        
        self._views_position = { }
        for section, tabs in (prewikka.views.events_section, prewikka.views.agents_section, prewikka.views.users_section,
                              prewikka.views.about_section):
            for tab, views in tabs:
                for view in views:
                    self._views_position[view] = section, tabs, tab
                    
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
            self._env.auth = Auth.AnonymousAuth(self._env)

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
        self._setupDataSet(object.dataset, request, user, view, parameters)

        return object
    
    def _cleanupView(self, view):
        del view.request
        del view.parameters
        del view.user
        del view.dataset
        del view.env
        
    def _setupDataSet(self, dataset, request, user, view=None, parameters={}):
        import prewikka.views

        init_dataset(dataset, self._env.config, request)
        
        if isinstance(self._env.auth, Auth.AnonymousAuth):
            sections = prewikka.views.events_section, prewikka.views.agents_section, prewikka.views.about_section
        else:
            sections = prewikka.views.events_section, prewikka.views.agents_section, prewikka.views.users_section, \
                       prewikka.views.about_section

        dataset["interface.sections"] = [ ]
        if user:
            for section_name, tabs in sections:
                viewable_tabs = 0
                for tab_name, views in tabs:
                    default_view = views[0]
                    if user.has(self._views[default_view]["permissions"]):
                        viewable_tabs += 1

                if viewable_tabs > 0:
                    dataset["interface.sections"].append((section_name,
                                                          utils.create_link(tabs[0][1][0])))
                    
        import prewikka.view

        if view and self._views_position.has_key(view["name"]):
            active_section, tabs, active_tab = self._views_position[view["name"]]
        elif isinstance(parameters, prewikka.view.RelativeViewParameters):
            active_section, tabs, active_tab = self._views_position[parameters["origin"]]
        else:
            active_section, tabs, active_tab = "", "", ""

        dataset["interface.active_section"] = active_section

        dataset["interface.tabs"] = [ ]
        if user:
            for tab, views in tabs:
                if user.has(self._views[views[0]]["permissions"]):
                    dataset["interface.tabs"].append((tab, utils.create_link(views[0])))
        
        dataset["interface.tabs"] = [ (tab, utils.create_link(views[0])) for tab, views in tabs ]
        dataset["interface.active_tab"] = active_tab

        dataset["prewikka.user"] = user
        dataset["prewikka.logout_link"] = (user and self._env.auth.canLogout()) and utils.create_link("logout") or None

    def _printDataSet(self, dataset, level=0):
        for key, value in dataset.items():
            print " " * level * 8,
            if isinstance(value, DataSet.DataSet):
                print key + ":"
                self._printDataSet(value, level + 1)
            else:
                print "%s: %s" % (key, value)
                    
    def _checkPermissions(self, request, view, user):
        if user and view.has_key("permissions"):
            if not user.has(view["permissions"]):
                self._env.log.warnings("Access to view forbidden", request, user)
                raise User.PermissionDeniedError(user.login, view["name"])

    def _getParameters(self, request, view, user):
        from prewikka.view import ParameterError

        parameters = view["parameters"](request.arguments) - [ "view" ]

        try:
            parameters.normalize(view["name"], user)
        except ParameterError, e:
            self._env.log.error("%s" % str(e), request, user)
            raise InvalidQueryError(request.getQueryString())

        return parameters
        
    def _getView(self, request, user):
        name = request.getView()
        try:
            return self._views[name]

        except KeyError:
            self._env.log.error("View '%s' does not exist" % name, request=request, user=user)
            raise InvalidQueryError(request.getQueryString())

    def checkAuth(self, request):
        return self._env.auth.getUser(request)

    def _setupError(self, error, request, user):
        error.dataset["query"] = request.getQueryString()
        self._setupDataSet(error.dataset, request, user)

        return error.dataset, error.template
    
    def process(self, request):
        try:
            user = None
            user = self.checkAuth(request)
            view = self._getView(request, user)

            self._checkPermissions(request, view, user)
            parameters = self._getParameters(request, view, user)
            view_object = self._setupView(view, request, parameters, user)

            self._env.log.info("Loading view", request, user)
            getattr(view_object, view["handler"])()

            dataset = view_object.dataset
            template_name = view["template"]

            self._cleanupView(view_object)
            
        except Error.PrewikkaError, e:
            self._setupDataSet(e.dataset, request, user)
            dataset, template_name = e.dataset, e.template
            
        except Exception, e:
            error = Error.SimpleError("prewikka internal error", str(e),
                                      display_traceback=not self._env.config.general.has_key("disable_error_traceback"))
            init_dataset(error.dataset, self._env.config, request)
            dataset, template_name = error.dataset, error.template
        
        #self._printDataSet(dataset)
        template = load_template(template_name, dataset)

        request.content = str(template)
        request.sendResponse()
