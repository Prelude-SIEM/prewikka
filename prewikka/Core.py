# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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

import copy

from prewikka import Config, Log, Prelude, ParametersNormalizer, User, \
    UserManagement, DataSet, Error, utils


class InvalidQueryError(Error.SimpleError):
    def __init__(self, query):
        Error.SimpleError.__init__(self, "query error", "invalid query " + query)



class PermissionDeniedError(Error.SimpleError):
    def __init__(self, user, action_name):
        Error.SimpleError.__init__(self, "permission denied",
                                   "user %s cannot access action %s" % (user, action_name))



class Environnement:
    def __init__(self, prelude_config):
        self.prelude = Prelude.Prelude(prelude_config)
        self.auth = None
        self.storage = None
        self.log = Log.Log()



class Core:
    def __init__(self):
        self._contents = { }
        self._content_names = [ ]
        self._config = Config.Config()
        self.env = Environnement(self._config.prelude)
        self._loadModules()
        self._initUserManagement()
        self._initAuth()

    def _initUserManagement(self):
        user_management = UserManagement.UserManagement(self.env)
        slots = user_management.slots
        for name, slot in slots.items():
            slot["permissions"] = [ User.PERM_USER_MANAGEMENT ]
            slot["handler"] = getattr(user_management, "handle_%s" % name)
            
        self._contents["configuration"] = { "sections": [("Configuration", user_management.default)],
                                            "default_slot": user_management.default,
                                            "slots": slots }
        self._content_names.append("configuration")
        
    def _initAuth(self):
        if self.env.auth and self.env.auth.canLogout():
            self._contents["logout"] = { "slots": { "logout": { "handler": self.env.auth.logout } } }
        
    def _loadModule(self, type, name, config):
        return __import__("prewikka/modules/%s/%s/%s" % (type, name, name)).load(self.env, config)

    def _loadModules(self):
        config = self._config

        if config.storage != None:
            self.env.storage = self._loadModule("storage", config.storage.name, config.storage)

        if config.auth != None:
            self.env.auth = self._loadModule("auth", config.auth.name, config.auth)
        
        for backend in config.logs:
            self.env.log.registerBackend(self._loadModule("log", backend.name, backend))

        for content in config.contents:
            self._contents[content.name] = self._loadModule("content", content.name, content)
            self._content_names.append(content.name)

    def _setupRequest(self, request, parameters):
        request.parameters = parameters
        request.dataset = DataSet.DataSet()
        self._setupDataSet(request.dataset, request)
        
    def _setupDataSet(self, dataset, request):
        dataset["document.title"] = "[PREWIKKA]"
        dataset["document.css_files"] = [ "lib/style.css" ]
        dataset["document.js_files"] = [ "lib/functions.js" ]
        dataset["prewikka.title"] = self._config.interface.getOptionValue("title", "Prelude management")
        dataset["prewikka.software"] = self._config.interface.getOptionValue("software", "Prewikka")
        dataset["prewikka.place"] = self._config.interface.getOptionValue("place", "company ltd.")
        dataset["prewikka.url.referer"] = request.getReferer()
        dataset["prewikka.url.current"] = request.getQueryString()
        dataset["prewikka.date"] = time.strftime("%A %B %d %Y")
        
        dataset["interface.sections"] = [ ]
        for name in self._content_names:
            content = self._contents[name]
            if content.has_key("sections"):
                for section, slot in content["sections"]:
                    dataset["interface.sections"].append((section,
                                                          utils.create_link("%s.%s" % (name, slot))))

        dataset["prewikka.user.login"] = request.user and request.user.login
        if self.env.auth.canLogout():
            dataset["prewikka.user.logout"] = utils.create_link("logout.logout")
        else:
            dataset["prewikka.user.logout"] = None

    def _printDataSet(self, dataset, level=0):
        for key, value in dataset.items():
            print " " * level * 8,
            if isinstance(value, DataSet.DataSet):
                print key + ":"
                self._printDataSet(value, level + 1)
            else:
                print "%s: %s" % (key, value)
            
    def _setupTemplate(self, template_class, dataset):
        template = template_class()
        for key, value in dataset.items():
            setattr(template, key, value)

        return template
        
    def _checkPermissions(self, request, slot):
        if request.user and slot.has_key("permissions"):
            required = slot["permissions"]
            if filter(lambda perm: request.user.has(perm), required) != required:
                self.env.log(Log.EVENT_ACTION_DENIED, request, request.handler_name)
                raise PermissionDeniedError(request.user.login, request.handler_name)

    def _normalizeParameters(self, request, slot):
        request.parameters = copy.copy(request.arguments)
        
        if slot.has_key("parameters"):
            try:
                slot["parameters"].normalize(request.parameters)
            except ParametersNormalizer.Error, e:
                self.env.log(Log.EVENT_INVALID_ACTION_PARAMETERS, request, str(e))
                raise InvalidQueryError(request.getQueryString())
        
    def _getContentSlot(self, request):
        if request.arguments.has_key("content"):
            content = request.arguments["content"]
            del request.arguments["content"]
        else:
            content = "main"

        try:
            if "." in content:
                content_name, slot_name = content.split(".")
            else:
                content_name = content
                slot_name = self._contents[content_name]["default_slot"]

            request.handler_name = "%s.%s" % (content_name, slot_name)

            return self._contents[content_name]["slots"][slot_name]

        except KeyError:
            self.env.log(Log.EVENT_INVALID_ACTION, request, content)
            raise InvalidQueryError(request.getQueryString())

    def checkAuth(self, request):
        if self.env.auth:
            login = self.env.auth.getLogin(request)
            permissions = self.env.storage and self.env.storage.getPermissions(login) or User.ALL_PERMISSIONS
        else:
            login = "anonymous"
            permissions = User.ALL_PERMISSIONS

        request.user = User.User(login, permissions)
    
    def process(self, request):
        self.env.log(Log.EVENT_QUERY, request, request.getQueryString())
        request.env = self.env

        try:
            self.checkAuth(request)
            slot = self._getContentSlot(request)
            self._checkPermissions(request, slot)
            self._normalizeParameters(request, slot)
                    
            self._setupRequest(request, request.parameters)

            try:
                slot["handler"](request)
            except Prelude.Error, e:
                raise Error.SimpleError("prelude internal error", str(e))

            dataset = request.dataset
            template_class = slot["template"]
            
        except Error.PrewikkaError, e:
            template_class = e.template_class
            dataset = e.dataset
            self._setupDataSet(dataset, request)

        #self._printDataSet(dataset)
        template = self._setupTemplate(template_class, dataset)

        request.content = str(template)
        request.sendResponse()
