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


from copy import copy


class ParameterError(Exception):
    pass


class InvalidParameterError(ParameterError):
    def __init__(self, name):
        ParameterError.__init__(self, "invalid parameter '%s'" % name)


class InvalidParameterValueError(ParameterError):
    def __init__(self, name, value):
        ParameterError.__init__(self, "invalid value '%s' for parameter '%s'" % (value, name))


class MissingParameterError(ParameterError):
    def __init__(self, name):
        ParameterError.__init__(self, "parameter '%s' is missing" % name)



class Parameters(dict):
    allow_extra_parameters = False
    
    def __init__(self, *args, **kwargs):
        apply(dict.__init__, (self, ) + args, kwargs)
        self._parameters = { }
        self.register()
        
    def register(self):
        pass
    
    def mandatory(self, name, type):
        self._parameters[name] = { "type": type, "mandatory": True }

    def optional(self, name, type, default=None):
        self._parameters[name] = { "type": type, "mandatory": False, "default": default }

    def normalize(self):
        for name, value in self.items():
            try:
                parameter_type = self._parameters[name]["type"]
            except KeyError:
                if self.allow_extra_parameters:
                    continue
                else:
                    raise InvalidParameterError(name)
        
            if parameter_type is list and not type(value) is list:
                value = [ value ]
            
            try:
                value = parameter_type(value)
            except (ValueError, TypeError):
                raise InvalidParameterValueError(name, value)
        
            self[name] = value

        for name in self._parameters.keys():
            if not self.has_key(name):
                if self._parameters[name]["mandatory"]:
                    raise MissingParameterError(name)
                elif self._parameters[name]["default"] != None:
                    self[name] = self._parameters[name]["default"]

    def __add__(self, src):
        dst = copy(self)
        dst.update(src)
        return dst

    def __sub__(self, keys):
        new = copy(self)
        for key in keys:
            try:
                del new[key]
            except KeyError:
                pass
        return new

    def copy(self):
        new = self.__class__()
        new.update(self)
        
        return new



class RelativeViewParameters(Parameters):
    def register(self):
        self.mandatory("origin", str)



class Views:
    view_initialized = False
    view_slots = { }

    def init(self, env):
        pass

    def get(self):
        for name, attrs in self.view_slots.items():
            attrs["name"] = name
            attrs["object"] = self
            attrs["handler"] = "render_" + name
        return self.view_slots



class View(Views):
    view_name = None
    view_parameters = None
    view_permissions = [ ]
    view_template = None

    def get(self):
        return { self.view_name: { "name": self.view_name,
                                   "object": self,
                                   "handler": "render",
                                   "parameters": self.view_parameters,
                                   "permissions": self.view_permissions,
                                   "template": self.view_template } }
