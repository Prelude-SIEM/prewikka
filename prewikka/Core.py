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

import prelude, preludedb

from prewikka import Config, Log, Database, IDMEFDatabase, ParametersNormalizer, \
     User, Auth, DataSet, Error, utils



class InvalidQueryError(Error.SimpleError):
    def __init__(self, query):
        Error.SimpleError.__init__(self, "query error", "invalid query " + query)



class PermissionDeniedError(Error.SimpleError):
    def __init__(self, user, action_name):
        Error.SimpleError.__init__(self, "permission denied",
                                   "user %s cannot access action %s" % (user, action_name))



class Core:
    def __init__(self):
        class Env: pass
        self._env = Env()
        self._env.config = Config.Config()
        self._env.db = Database.Database(self._env.config.database)
        self._env.idmef_db = IDMEFDatabase.IDMEFDatabase(self._env.config.idmef_database)
        self._env.auth = Auth.AnonymousAuth()
        self._env.log = Log.Log()
        self._initHostCommands()
        self._loadViews()
        self._loadModules()
        self._initAuth()

    def _initHostCommands(self):
        self._env.host_commands = { }
        for command in "whois", "traceroute":
            path = distutils.spawn.find_executable(command)
            if path:
                self._env.host_commands[command] = path
            
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
        module = "prewikka/modules/%s/%s/%s" % (type, name, name)
        return __import__(module).load(self._env, config)

    def _loadModules(self):
        config = self._env.config

        if config.auth:
            self._env.auth = self._loadModule("auth", config.auth.name, config.auth)
        
        for backend in config.logs:
            self._env.log.registerBackend(self._loadModule("log", backend.name, backend))

    def _setupView(self, view, request, parameters, user):
        object = view["object"]
        if not object.view_initialized:
            object.init(self._env)
            object.view_initialized = True
        object.request = request
        object.parameters = parameters
        object.user = user
        object.dataset = DataSet.DataSet()
        object.env = self._env
        self._setupDataSet(object.dataset, request, user, view, parameters)

    def _cleanupView(self, view):
        object = view["object"]
        del object.request
        del object.parameters
        del object.user
        del object.dataset
        del object.env
        
    def _setupDataSet(self, dataset, request, user, view=None, parameters={}):
        import prewikka.views
        
        interface = self._env.config.interface
        dataset["document.title"] = "[PREWIKKA]"
        dataset["document.css_files"] = [ "lib/style.css" ]
        dataset["document.js_files"] = [ "lib/functions.js" ]
        dataset["prewikka.title"] = interface.getOptionValue("title", "Prelude management")
        dataset["prewikka.software"] = interface.getOptionValue("software", "Prewikka")
        dataset["prewikka.place"] = interface.getOptionValue("place", "company ltd.")
        dataset["prewikka.url.referer"] = request.getReferer()
        dataset["prewikka.url.current"] = request.getQueryString()
        dataset["prewikka.date"] = time.strftime("%A %B %d %Y")

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

        if user:
            dataset["prewikka.user.login"] = user and user.login or None
            dataset["prewikka.user.logout"] = self._env.auth.canLogout() and utils.create_link("logout") or None

    def _printDataSet(self, dataset, level=0):
        for key, value in dataset.items():
            print " " * level * 8,
            if isinstance(value, DataSet.DataSet):
                print key + ":"
                self._printDataSet(value, level + 1)
            else:
                print "%s: %s" % (key, value)
            
    def _setupTemplate(self, name, dataset):
        template = getattr(__import__("prewikka/templates/" + name), name)()
        
        for key, value in dataset.items():
            setattr(template, key, value)

        return template
        
    def _checkPermissions(self, request, view, user):
        if user and view.has_key("permissions"):
            if not user.has(view["permissions"]):
                self._env.log(Log.EVENT_VIEW_FORBIDDEN, request, view, user)
                raise User.PermissionDeniedError(user.login, view["name"])

    def _getParameters(self, request, view, user):
        from prewikka.view import ParameterError

        parameters = view["parameters"](request.arguments) - [ "view" ]

        try:
            parameters.normalize()
        except ParameterError, e:
                self._env.log(Log.EVENT_INVALID_PARAMETERS, request, view, details=str(e))
                raise InvalidQueryError(request.getQueryString())

        return parameters
        
    def _getView(self, request, user):
        name = request.arguments.get("view", "alert_listing")

        try:
            return self._views[name]

        except KeyError:
            self._env.log(Log.EVENT_INVALID_VIEW, request=request, user=user)
            raise InvalidQueryError(request.getQueryString())

    def checkAuth(self, request):
        return self._env.auth.getUser(request)
    
    def process(self, request):
        self._env.log(Log.EVENT_QUERY, request)
        
        try:
            user = None
            user = self.checkAuth(request)
            view = self._getView(request, user)
            self._checkPermissions(request, view, user)
            parameters = self._getParameters(request, view, user)
            
            self._setupView(view, request, parameters, user)

            self._env.log(Log.EVENT_RENDER_VIEW, request, view, user)

            try:
                getattr(view["object"], view["handler"])()
            except (prelude.PreludeError, preludedb.PreludeDBError), e:
                raise Error.SimpleError("prelude internal error", str(e))

            dataset = view["object"].dataset
            template_name = view["template"]

            self._cleanupView(view)
            
        except Error.PrewikkaError, e:
            template_name = e.template
            dataset = e.dataset
            self._setupDataSet(dataset, request, user)

        #self._printDataSet(dataset)
        template = self._setupTemplate(template_name, dataset)

        request.content = str(template)
        request.sendResponse()
