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
import os, os.path

import copy

from prewikka import Config, Log, Prelude, Action, Interface, User, \
    UserManagement, DataSet, Error, utils


class InvalidQueryError(Error.SimpleError):
    def __init__(self, query):
        Error.SimpleError.__init__(self, "query error", "invalid query " + query)



class PermissionDeniedError(Error.SimpleError):
    def __init__(self, user, action_name):
        Error.SimpleError.__init__(self, "permission denied",
                                   "user %s cannot access action %s" % (user, action_name))


class Core:
    def __init__(self):
        self.content_modules = { }
        self._content_module_names = [ ]
        self._actions = { }
        self._default_action = None
        self._login_action = None
        self._config = Config.Config()
        self.log = Log.Log()
        self.interface = Interface.Interface(self, self._config.get("interface", { }))
        self.prelude = Prelude.Prelude(self._config["prelude"])
        self.storage = None
        self.auth = None
        self._initModules()

        if self.storage:
            user_management = UserManagement.UserManagement(self)
            self.registerActionGroup(user_management)
        
        if self.auth and self.auth.canLogout():
            class LogoutAction(Action.Action):
                def __init__(self, auth):
                    Action.Action.__init__(self, "logout")
                    self._auth = auth
                
                def process(self, request):
                    self._auth.logout(request)

            action = LogoutAction(self.auth)
            self.registerActionGroup(action)
            self.interface.registerQuickAccessor("logout", action.slots["process"].path, Action.ActionParameters())

    def registerActionGroup(self, action_group):
        self._actions[action_group.name] = action_group

    def registerAction(self, action):
        self.registerActionGroup(action)

    def shutdown(self):
        # Core references objects that themself reference Core, those circular
        # references mean that garbage collector won't destroy those objects.
        # Thus, code that use Core must call the shutdown method (that remove
        # Core references) so that cleanup code (__del__ object methods) will be called
        self.content_modules = None
        self._content_module_names = None
        self._config = None
        self.interface = None
        self.prelude = None
        self.auth = None

    def setDefaultAction(self, action):
        self._default_action = action

    def registerAuth(self, auth):
        self.auth = auth

    def registerStorage(self, storage):
        self.storage = storage

    def _initModules(self):
        base_dir = "prewikka/modules/"
        for mod_name in self._config.getModuleNames():
            try:
                file = base_dir + mod_name + "/" + mod_name
                module = __import__(file)
                module.load(self, self._config.modules.get(mod_name, { }))
            except ImportError:
                print >> sys.stderr, "cannot load module named %s (%s)" % (mod_name, file)
                raise

    def _setupRequest(self, request, parameters):
        request.prelude = self.prelude
        request.parameters = parameters
        request.dataset = DataSet.DataSet()
        self._setupDataSet(request.dataset, request)
        
    def _setupDataSet(self, dataset, request):
        interface = self.interface
        dataset["document.title"] = "[PREWIKKA]"
        dataset["document.css_files"] = [ "lib/style.css" ]
        dataset["document.js_files"] = [ "lib/functions.js" ]
        dataset["prewikka.title"] = interface.getTitle()
        dataset["prewikka.software"] = interface.getSoftware()
        dataset["prewikka.place"] = interface.getPlace()
        dataset["prewikka.url.referer"] = request.getReferer()
        dataset["prewikka.url.current"] = request.getQueryString()
        dataset["interface.quick_accessors"] = map(lambda qa: (qa[0], utils.create_link(qa[1], qa[2])),
                                                   interface.getQuickAccessors())
        dataset["interface.sections"] = interface.getSections()
        
    def _setupTemplate(self, template_class, dataset):
        template = template_class()
        for key, value in dataset.items():
            setattr(template, key, value)

        return template
        
    def _getActionNameAndArguments(self, request):
        arguments = copy.copy(request.arguments)
        if arguments.has_key("action"):
            action_name = arguments["action"]
            del arguments["action"]
        else:
            action_name = None

        return action_name, arguments

    def _getActionSlot(self, request, action_name):
        if not action_name:
            return self._default_action
        
        try:
            group_name, slot_name = Action.ActionGroup.getGroupAndSlot(action_name)
            return self._actions[group_name].slots[slot_name]
        except ValueError, KeyError:
            self.log(Log.EVENT_INVALID_ACTION, request, action_name)
            raise InvalidQueryError(request.getQueryString())
        
    def _checkPermissions(self, slot, request):
        if request.user:
            required = slot.permissions
            if filter(lambda perm: request.user.has(perm), required) != required:
                self.log(Log.EVENT_ACTION_DENIED, request, slot.path)
                raise PermissionDeniedError(request.user.login, slot.path)
        
    def processAction(self, slot, request):
        self._checkPermissions(slot, request)
        
        return slot.handler(request)

    def processDefaultAction(self, request):
        request.parameters = self._default_action.parameters()
        
        return self.processAction(self._default_action, request)

    def checkAuth(self, request):
        if self.auth:
            login = self.auth.getLogin(request)
            permissions = self.storage and self.storage.getPermissions(login) or User.ALL_PERMISSIONS
        else:
            login = "anonymous"
            permissions = User.ALL_PERMISSIONS

        request.user = User.User(login, permissions)
    
    def process(self, request):
        self.log(Log.EVENT_QUERY, request, request.getQueryString())

        request.log = self.log

        try:
            self.checkAuth(request)
            
            action_name, arguments = self._getActionNameAndArguments(request)
            slot = self._getActionSlot(request, action_name)
            parameters = slot.parameters()
            
            try:
                parameters.populate(arguments)
                parameters.check()
            except Action.ActionParameterError, e:
                self.log(Log.EVENT_INVALID_ACTION_PARAMETERS, request, str(e))
                raise InvalidQueryError(request.getQueryString())
                    
            self._setupRequest(request, parameters)

            try:
                template_class = self.processAction(slot, request)
            except Prelude.Error, e:
                raise Error.SimpleError("prelude internal error", str(e))

            dataset = request.dataset
            
        except Error.PrewikkaError, e:
            template_class = e.template_class
            dataset = e.dataset
            self._setupDataSet(dataset, request)

        template = self._setupTemplate(template_class, dataset)

        request.content = str(template)
        request.sendResponse()
