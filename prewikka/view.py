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
import Error, Log

class ParameterError(Exception):
        pass

class InvalidParameterError(Error.PrewikkaUserError):
    def __init__(self, name):
        Error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                               "Parameter '%s' is not valid" % name, log=Log.WARNING)


class InvalidParameterValueError(Error.PrewikkaUserError):
    def __init__(self, name, value):
        Error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                               "Invalid value '%s' for parameter '%s'" % (value, name), log=Log.WARNING)


class MissingParameterError(Error.PrewikkaUserError):
    def __init__(self, name):
        Error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                         "Required parameter '%s' is missing" % name, log=Log.WARNING)



class Parameters(dict):
    allow_extra_parameters = False

    def __init__(self, *args, **kwargs):
        apply(dict.__init__, (self, ) + args, kwargs)
        self._default = {}
        self._parameters = { }
        self.register()
        self.optional("_error_back", str)
        self.optional("_error_retry", str)
        self.optional("_save", str)

    def register(self):
        pass

    def mandatory(self, name, type):
        self._parameters[name] = { "type": type, "mandatory": True, "save": False }

    def optional(self, name, type, default=None, save=False):
        if default is not None:
            self._default[name] = default

        self._parameters[name] = { "type": type, "mandatory": False, "default": default, "save": save }

    def _parseValue(self, name, value):
        parameter_type = self._parameters[name]["type"]
        if parameter_type is list and not type(value) is list:
            value = [ value ]

        try:
            value = parameter_type(value)
        except (ValueError, TypeError):
            raise InvalidParameterValueError(name, value)

        return value

    def normalize(self, view, user):
        do_load = True

        for name, value in self.items():
            try:
                value = self._parseValue(name, value)
            except KeyError:
                if self.allow_extra_parameters:
                    continue

                raise InvalidParameterError(name)

            if not self._parameters.has_key(name):
                do_load = False

            if self._parameters[name]["save"] and self.has_key("_save"):
                user.setConfigValue(view, name, value)

            self[name] = value

        # Go through unset parameters.
        # - Error out on mandatory parameters,
        # - Load default value for optional parameters that got one.
        # - Load last user value for parameter.

        for name in self._parameters.keys():
            got_param = self.has_key(name)
            if not got_param:
                if self._parameters[name]["mandatory"]:
                    raise MissingParameterError(name)

                elif self._parameters[name]["default"] != None:
                    self[name] = self._parameters[name]["default"]

            if self._parameters[name]["save"]:
                try: value = self._parseValue(name, user.getConfigValue(view, name))
                except KeyError:
                    continue

                self._default[name] = value
                if do_load and not got_param:
                    self[name] =  self._default[name]

        try: self.pop("_save")
        except: pass

        return do_load

    def getDefaultValues(self):
        return self._default

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
