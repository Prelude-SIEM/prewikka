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
import os

import copy
import urllib
import cgi

from prewikka import Views, Log

class Error(Exception):
    pass



class ActionError(Error):
    pass



class ActionParameterError(Error):
    pass


class ActionDeniedError(Error):
    pass


class ActionParameterInvalidError(ActionParameterError):
    def __init__(self, name):
        self._name = name
        
    def __str__(self):
        return "invalid parameter '%s'" % self._name



class ActionParameterInvalidTypeError(ActionParameterError):
    def __init__(self, name, value, required_type):
        self._name = name
        self._value = value
        self._required_type = required_type
        
    def __str__(self):
        return "invalid type %s for parameter '%s', %s required" % \
               (str(type(self._value)), self._name, str(self._required_type))



class ActionParameterMissingError(ActionParameterError):
    def __init__(self, name):
        self._name = name
        
    def __str__(self):
        return "parameter '%s' is missing" % self._name



class ActionParameterAlreadyRegisteredError(ActionParameterError):
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "parameter '%s' is already registered" % self._name



def get_action_name(action):
    if isinstance(action, Action):
        return action.getName()
    return "%s.%s.%s" % (action.im_func.__module__, action.im_class.__name__, action.im_func.__name__)



class ConfigView:
    def __init__(self, core):
        self.active_section = "Configuration"
        self.tabs = core.interface._configuration



class Interface:
    def __init__(self, core, config):
        self._sections = [ ]
        self._special_actions = [ ]
        self._actions = { }
        self._default_action = None
        self._login_action = None
        self._core = core
        self._software = config.getOptionValue("software", "Prewikka")
        self._place = config.getOptionValue("place", "")
        self._title = config.getOptionValue("title", "Prelude management")
        self._configuration = [ ]
        
    def registerSpecialAction(self, name, action, parameters):
        self._special_actions.append((name, action, parameters))
        
    def getSpecialActions(self):
        return self._special_actions
    
    def getSections(self):
        return self._sections
    
    def getDefaultAction(self):
        return self._default_action
    
    def getSoftware(self):
        return self._software

    def getPlace(self):
        return self._place

    def getTitle(self):
        return self._title
    
    def registerSection(self, name, action):
        self._sections.append((name, action))
        
    def registerConfigurationSection(self, name, action):
        if not self._configuration:
            self.registerSection("Configuration", action)
        self._configuration.append((name, action))
        
    def registerAction(self, action, parameters, capabilities, default=False):
        name = get_action_name(action)
        
        self._actions[name] = { "action": action, "parameters": parameters, "capabilities": capabilities }
        if default:
            self._default_action = name
        
        return name
        
    def registerLoginAction(self, action, parameters):
        name = self.registerAction(action, parameters, [ ])
        self._login_action = name
        
    def callAction(self, action, core, parameters, request):
        if isinstance(action, Action):
            return action.process(core, parameters, request)
        return action(core, parameters, request)
    
    def forwardToAction(self, action, core, parameters, request):
        try:
            self.checkActionCapability(request.user, self._actions[get_action_name(action)]["capabilities"])
        except ActionDeniedError:
            return Views.ErrorView, "Permission Denied."
        
        return self.callAction(action, core, parameters, request)
    
    def forwardToDefaultAction(self, core, request):
        registered = self._actions[self._default_action]
        action = registered["action"]
        parameters = registered["parameters"]()
        
        return self.forwardToAction(action, core, parameters, request)

    def _buildView(self, view_class, data):
        view = view_class(self._core)
        view.build(data)
        
        return str(view)
    
    def checkActionCapability(self, user, required):
        if filter(lambda cap: user.hasCapability(cap), required) != required:
            raise ActionDeniedError
        
    def processAction(self, name, arguments, request):
        self._core.log.event(Log.EVENT_ACTION, request, name)
        
        try:
            registered = self._actions[name]
        except KeyError:
            self._core.log.event(Log.EVENT_INVALID_ACTION, request, name)
            return self._buildView(Views.ErrorView, "unknown action name %s" % name)
        
        if request.user:
            try:
                self.checkActionCapability(request.user, registered["capabilities"])
            except ActionDeniedError:
                return self._buildView(Views.ErrorView, "Permission Denied.")
        
        action = registered["action"]
        parameters = registered["parameters"]()
        
        try:
            parameters.populate(arguments)
            parameters.check()
        except ActionParameterError, e:
            self._core.log.event(Log.EVENT_INVALID_ACTION_PARAMETERS, request, str(e))
            return self._buildView(Views.ErrorView, cgi.escape(str(e)))
        
        view = self.callAction(action, self._core, parameters, request)

        return str(view)
    
    def processDefaultAction(self, arguments, request):
        return self.processAction(self._default_action, arguments, request)

    def process(self, request):
        arguments = copy.copy(request.arguments)
        if arguments.has_key("action"):
            action = arguments["action"]
            del arguments["action"]
        else:
            action = self._default_action
            
        if action == self._login_action:
            return self.processAction(action, arguments, request)
        
        if self._core.auth:        
            view = self._core.auth.check(request)
            if view:
                return view
            
        if action is None:
            return self.processDefaultAction(arguments, request)
        
        return self.processAction(action, arguments, request)



class Action(object):
    def process(self, core, parameters):
        pass
    
    def getName(self):
        return self.__module__ + "." + self.__class__.__name__



class ActionParameters:
    def __init__(self, parameters=None):
        self._parameters = { }
        self._values = { }
        self.register()
        if parameters:
            for name in self._parameters.keys():
                if parameters.hasParameter(name):
                    self[name] = parameters[name]
        
    def register(self):
        pass
    
    def registerParameter(self, name, type):
        if self._parameters.has_key(name):
            raise ActionParameterAlreadyRegisteredError(name)
        
        self._parameters[name] = type
        
    def __setitem__(self, name, value):
        try:
            parameter_type = self._parameters[name]
        except KeyError:
            raise ActionParameterInvalidError(name)
        
        if parameter_type is list and not type(value) is list:
            value = [ value ]
            
        try:
            value = parameter_type(value)
        except ValueError:
            raise ActionParameterInvalidTypeError(name, value, parameter_type)
        
        self._values[name] = value
        
    def __getitem__(self, name):
        return self._values[name]

    def __delitem__(self, name):
        del self._values[name]

    def get(self, name, default_value=None):
        return self._values.get(name, default_value)

    def hasParameter(self, name):
        return self._values.has_key(name)

    def populate(self, query):
        for name, value in query.items():
            self[name] = value
        
    def check(self):
        return True

    def getNames(self, ignore=[]):
        return filter(lambda name: not name in ignore, self._values.keys())

    def items(self):
        return self._values.items()

    def debug(self):
        content = ""
        for key, value in self._values.items():
            content += "%s: %s\n" % (key, value)
        
        return content

    def __str__(self):
        return urllib.urlencode(self._values)

    def __copy__(self):
        new = self.__class__()
        new._parameters = copy.copy(self._parameters)
        new._values = copy.copy(self._values)
        
        return new
