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

import copy
import urllib

class Error(Exception):
    pass



class ActionError(Error):
    pass



class ActionParameterError(Error):
    pass



class InvalidActionParameterError(ActionParameterError):
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return "invalid parameter '%s'" % self._name



class InvalidTypeActionParameterError(ActionParameterError):
    def __init__(self, parameter, expected_type):
        self._parameter = parameter
        self._expected_type = expected_type

    def __str__(self):
        return "invalid type '%s' for parameter '%s', '%s' expected" % (type(self._parameter), self._parameter, self.expected_type)



class AlreadyRegisteredActionParameterError(ActionParameterError):
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

    def getSoftware(self):
        return self._software

    def getPlace(self):
        return self._place

    def getTitle(self):
        return self._title

    def registerSection(self, name, action):
        self._sections.append((name, action))

    def registerAction(self, action, parameters, default=False):
        registered = self._actions[action.getId()] = { "action": action, "parameters": parameters }
        if default:
            self._default_action = registered

    def process(self, action_name, query):
        if action_name:
            registered = self._actions[action_name]
        else:
            registered = self._default_action

        action = registered["action"]
        parameters = registered["parameters"]()
        parameters.populate(query)
        view_class, data = action.process(self._core, parameters)
        view = view_class(self._core, data)
        view.init()
        view.build()
        
        return str(view)
                


class Action(object):
    def process(self, core, parameters):
        pass

    def getId(self):
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
            raise AlreadyRegisteredActionParameterError
        self._parameters[name] = type

    def __setitem__(self, name, value):
        parameter_type = self._parameters[name]
        
        if parameter_type is list and not type(value) is list:
            value = [ value ]
            
        try:
            value = parameter_type(value)
        except ValueError:
            raise InvalidTypeActionParameterError(name, parameter_type)
        
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
