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


import copy
import urllib

from prewikka import Log


class ActionParameterError(Exception):
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
    
    def registerParameter(self, name, type, required=False):
        if self._parameters.has_key(name):
            raise ActionParameterAlreadyRegisteredError(name)
        
        self._parameters[name] = { "type": type, "required": required }
        
    def __setitem__(self, name, value):
        try:
            parameter_type = self._parameters[name]["type"]
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
        for name in self._parameters.keys():
            if self._parameters[name]["required"] and not self.hasParameter(name):
                raise ActionParameterMissingError(name)
            
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



class ActionSlot:
    def __init__(self, path, name, parameters, permissions, handler):
        self.path = path
        self.name = name
        self.parameters = parameters
        self.permissions = permissions
        self.handler = handler



class ActionGroup(object):
    def __init__(self, name=None):
        self.slots = { }
        self.name = name or self.__module__.replace("/", ".").split(".")[-2] + "." + self.__class__.__name__

    def registerSlot(self, name, parameters=ActionParameters, permissions=[], handler=None):
        if not handler:
            handler = getattr(self, "handle_" + name)
        
        slot = ActionSlot(":".join((self.name, name)), name, parameters, permissions, handler)
        self.slots[name] = slot

        return slot

    def getGroupAndSlot(s):
        return s.split(":")

    getGroupAndSlot = staticmethod(getGroupAndSlot)



class Action(ActionGroup):
    parameters = ActionParameters
    permissions = [ ]
    
    def __init__(self, name=None):
        ActionGroup.__init__(self, name)
        slot = self.registerSlot("process", self.parameters, self.permissions, self.process)
        self.slot = slot
        self.path = slot.path
        
    def process(self, request):
        pass
