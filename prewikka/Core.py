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

from prewikka import Config, Log, Prelude, Action, Interface, Error


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
        self.auth = None
        self._initModules()

    def registerActionGroup(self, action_group):
        self._actions[action_group.name] = action_group

    def registerAction(self, action):
        self.registerActionGroup(action)

    def setLoginAction(self, action):
        self._login_action = action

    def setDefaultAction(self, action):
        self._default_action = action

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

    def registerAuth(self, auth):
        self.registerActionGroup(auth)
        self.auth = auth

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
        request.log = self.log
        request.prelude = self.prelude
        request.parameters = parameters
        
        def dummy():
            return self.processDefaultAction(request)
        
        request.forwardToDefaultAction = dummy
        
    def _setupView(self, view, request):
        interface = self.interface
        view.setInfoTitle(interface.getTitle())
        view.setInfoSoftware(interface.getSoftware())
        view.setInfoPlace(interface.getPlace())
        view.addSections(interface.getSections())
        view.setConfiguration(interface.getConfiguration())
        view.addQuickAccessors(interface.getQuickAccessors())
        view.referer = request.getReferer()
        view.current = request.getQueryString()
        
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
        
    def _checkCapabilities(self, slot, request):
        if request.user:
            required = slot.capabilities
            if filter(lambda cap: request.user.hasCapability(cap), required) != required:
                self.log(Log.EVENT_ACTION_DENIED, request, slot.path)
                raise PermissionDeniedError(request.user.getLogin(), slot.path)
        
    def processAction(self, slot, request):
        self._checkCapabilities(slot, request)
        
        return slot.handler(request)

    def processDefaultAction(self, request):
        request.parameters = self._default_action.parameters()
        
        return self.processAction(self._default_action, request)
    
    def process(self, request):
        self.log(Log.EVENT_QUERY, request, request.getQueryString())

        try:
            action_name, arguments = self._getActionNameAndArguments(request)
            slot = self._getActionSlot(request, action_name)
            
            if self.auth and slot != self._login_action:
                self.auth.check(request)
                
            parameters = slot.parameters()
            try:
                parameters.populate(arguments)
                parameters.check()
            except Action.ActionParameterError, e:
                self.log(Log.EVENT_INVALID_ACTION_PARAMETERS, request, str(e))
                raise InvalidQueryError(request.getQueryString())
                    
            self._setupRequest(request, parameters)

            try:
                view = self.processAction(slot, request)
            except Prelude.Error, e:
                raise Error.SimpleError("prelude internal error", str(e))
                
            
        except Error.BaseError, view:
            pass

        self._setupView(view, request)

        request.content = str(view)
        request.sendResponse()
