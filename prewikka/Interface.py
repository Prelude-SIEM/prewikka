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

from prewikka import Views

class Error(Exception):
    pass



class ActionError(Error):
    pass



class ActionParameterError(Error):
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



class Interface:
    def __init__(self, core, config):
        self._sections = [ ]
        self._actions = { }
        self._default_action = None
        self._core = core
        self._software = config.get("software", "Prewikka")
        self._place = config.get("place", "")
        self._title = config.get("title", "Prelude management")
        
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

    def registerAction(self, action, parameters, default=False):
        name = action.getName()
        self._actions[name] = { "action": action, "parameters": parameters }
        if default:
            self._default_action = name
        
    def processAction(self, name, arguments, request):
        try:
            registered = self._actions[name]
            action = registered["action"]
            parameters = registered["parameters"]()
            parameters.populate(arguments)
            parameters.check()
        except KeyError:
            data = "unknown action name %s" % name
            self._core.log.invalidQuery(request, data)
            view_class = Views.ErrorView
        except ActionParameterError, e:
            self._core.log.invalidQuery(request, str(e))
            view_class = Views.ErrorView
            data = cgi.escape(str(e))
        else:
            view_class, data = action.process(self._core, parameters, request)
        
        view = view_class(self._core)
        view.build(data)

        return str(view)

    def processDefaultAction(self, arguments, request):
        return self.processAction(self._default_action, arguments, request)
    
    def processLogin(self, arguments, request):
        import Auth
        
        auth = self._core.auth
        login = arguments["login"]
        password = arguments["password"]
        try:
            auth.login(login, password, request)
        except (Auth.LoginError, Auth.AuthError):
            return auth.getLoginScreen(request)
        
        return self.processDefaultAction({ }, request)

    def process(self, request):
        from prewikka import Auth
        
        arguments = copy.copy(request.arguments)
        action = arguments.pop("action", None)
        auth = self._core.auth
        
        if action == "login":
            return self.processLogin(arguments, request)
        
        try:
            name = auth.check(request)
        except Auth.AuthError:
            return auth.getLoginScreen(request)
        
        if action is None:
            return self.processDefaultAction(arguments, request)
        
        return self.processAction(action, arguments, request)



class Action(object):
    def process(self, core, parameters):
        pass
    
    def getName(self):
        return self.__module__ + "." + self.__class__.__name__

    def test(self):
        return self.getId()



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

    def __str__(self):
        return urllib.urlencode(self._values)

    def __copy__(self):
        new = self.__class__()
        new._parameters = copy.copy(self._parameters)
        new._values = copy.copy(self._values)
        
        return new
