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


class Error(Exception):
    pass


class InvalidParameterError(Error):
    def __init__(self, name):
        Error.__init__(self, "Invalid parameter '%s'" % name)


class InvalidValueError(Error):
    def __init__(self, name, value):
        Error.__init__(self, "Invalid value '%s' for parameter '%s'" % (value, name))


class MissingParameterError(Error):
    def __init__(self, name):
        Error.__init__(self, "Missing parameter '%s'" % name)
    

class ParametersNormalizer:
    allow_extra_parameters = False
    
    def __init__(self):
        self._parameters = { }
        self.register()
        
    def register(self):
        pass
    
    def mandatory(self, name, type):
        self._parameters[name] = { "type": type, "mandatory": True }

    def optional(self, name, type, default=None):
        self._parameters[name] = { "type": type, "mandatory": False, "default": default }

    def normalize(self, parameters):
        for name, value in parameters.items():
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
            except ValueError:
                raise InvalidValueError(name, value)
        
            parameters[name] = value

        for name in self._parameters.keys():
            if not parameters.has_key(name):
                if self._parameters[name]["mandatory"]:
                    raise MissingParameterError(name)
                elif self._parameters[name]["default"] != None:
                    parameters[name] = self._parameters[name]["default"]
