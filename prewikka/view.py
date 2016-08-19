# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import operator, json, time
from copy import copy
from prewikka import pluginmanager, template, usergroup, error, log, utils, env, hookmanager
from prewikka.response import PrewikkaResponse


logger = log.getLogger(__name__)


class ParameterError(Exception):
        pass

class InvalidParameterError(error.PrewikkaUserError):
    def __init__(self, name):
        error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                               _("Parameter '%s' is not valid") % name, log_priority=log.WARNING)


class InvalidParameterValueError(error.PrewikkaUserError):
    def __init__(self, name, value):
        error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                               _("Invalid value '%(value)s' for parameter '%(name)s'") % {'value':value, 'name':name}, log_priority=log.WARNING)


class MissingParameterError(error.PrewikkaUserError):
    def __init__(self, name):
        error.PrewikkaUserError.__init__(self, _("Parameters Normalization failed"),
                                         _("Required parameter '%s' is missing") % name, log_priority=log.WARNING)

class InvalidViewError(error.PrewikkaUserError):
    code = 404

    def __init__(self, message):
        error.PrewikkaUserError.__init__(self, _("Invalid view"), message, log_priority=log.ERROR)



class ParameterDesc(object):
    """ Describe a HTTP parameter """

    def __init__(self, name, type, mandatory=False, default=None, save=False, general=False):
        """ Args :
        name : Name of the parameter
        type : Type of the parameter (int, str, list, ...)
        mandatory : True if the parameter is mandatory
        default : Specify a default value
        save : True if the parameter is store in BDD to when set
        general : True if the parameter is available for all the view """

        self.name = name
        self.save = save
        self.general = general
        self.default = default
        self.mandatory = mandatory

        if type is list:
            self.type = [ str ]
        else:
            self.type = type

    def has_default(self):
        """ Return True if this parameter has a default value """
        return self.default is not None

    def _mklist(self, value):
        """ Return the value as a list """

        if not isinstance(value, list):
            return [ value ]

        return value

    def parse(self, value):
        """ Return the value according to the parameter's type """

        try:
            if isinstance(self.type, list):
                value = map(self.type[0], self._mklist(value))
            else:
                value = self.type(value)

        except (ValueError, TypeError):
            raise InvalidParameterValueError(self.name, value)

        return value


class Parameters(dict):
    allow_extra_parameters = False

    def __init__(self, view, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        self._hard_default = {}
        self._default = {}
        self._parameters = { }

        self.register()
        self.optional("_save", str)
        self.optional("_download", str)

        list(hookmanager.trigger("HOOK_%s_PARAMETERS_REGISTER" % view.view_id.upper(), self))

    def register(self):
        pass

    def mandatory(self, name, type):
        self._parameters[name] = ParameterDesc(name, type, mandatory=True, save=True)

    def optional(self, name, type, default=None, save=False, general=False):
        if default is not None:
            self._default[name] = self._hard_default[name] = default

        self._parameters[name] = ParameterDesc(name, type, mandatory=False, default=default, save=save, general=general)

    def normalize(self, view, user):
        do_load = True
        do_save = "_save" in self

        for name, value in self.items():
            param = self._parameters.get(name)
            if not param:
                if not(self.allow_extra_parameters):
                    raise InvalidParameterError(name)

                continue

            if not name in self._parameters or param.mandatory is False:
                do_load = False

            value = param.parse(value)
            if user and param.save and do_save:
                if param.general:
                    user.set_property(name, value)
                else:
                    user.set_property(name, value, view=view)

            self[name] = value

        # Go through unset parameters.
        # - Error out on mandatory parameters,
        # - Load default value for optional parameters that got one.
        # - Load last user value for parameter.

        for name in set(self._parameters.keys()) - set(self.keys()):
            param = self._parameters[name]

            if param.mandatory:
                raise MissingParameterError(name)

            elif param.has_default():
                self[name] = param.default

            if not param.save or not user:
                continue

            if param.general:
                save_view = None
            else:
                save_view = view

            if do_save:
                user.del_property(name, view=save_view)
            else:
                if not name in user.configuration.get(save_view, {}):
                    continue

                value = param.parse(user.get_property(name, view=save_view))

                self._default[name] = value
                if do_load:
                    self[name] = value

        # In case the view was dynamically added through HOOK_VIEW_LOAD, the hook isn't available
        list(hookmanager.trigger("HOOK_%s_PARAMETERS_NORMALIZE" % view.upper(), self))

        self.pop("_save", None)
        return do_load

    def handleLists(self):
        pass

    def handleList(self, list_name, prefix, separator="_", ordered=False, has_value=True):
        """
        Return the object list from POST parameters
        """
        obj_list = [ ]
        obj_dict = { }
        obj_order = [ ]
        for key, value in self.items():
            if not key.startswith('%s%s' % (prefix, separator)):
                continue

            field = key[len(prefix) + len(separator):]
            if ordered:
                l = key[len(prefix) + len(separator):].split(separator, 1)
                field = l[0]
                order = len(l) == 2 and int(l[1]) or 0
            else:
                field = key[len(prefix) + len(separator):]
                order = 0


            if order not in obj_dict:
                obj_dict[order] = { } if has_value else [ ]
                obj_order.append(order)
            if has_value:
                obj_dict[order][field] = value
            else:
                obj_dict[order].append(field)
            self.pop(key)

        obj_order.sort()
        for obj in obj_order:
            obj_list.append(obj_dict[obj])

        if ordered or not obj_list:
            self[list_name] = obj_list
        elif has_value:
            self[list_name] = obj_list[0].items()
        else:
            self[list_name] = obj_list[0]

    def getDefault(self, param, usedb=True):
        return self.getDefaultValues(usedb)[param]

    def getDefaultValues(self, usedb=True):
        if not usedb:
            return self._hard_default
        else:
            return self._default

    def isSaved(self, param):
        if not param in self._parameters:
            return False

        if not self._parameters[param].save:
            return False

        val1 = self._hard_default[param]
        val2 = self[param]

        if type(val1) is list:
            val1.sort()

        if type(val2) is list:
            val2.sort()

        if val1 == val2:
            return False

        return True

    def isDefault(self, param, usedb=True):
        if not usedb:
            return self._hard_default.has_key(param)
        else:
            return self._default.has_key(param)

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



_VIEWS = {}
_sentinel = object()

def getViewPath(view_id, default=_sentinel):
    view_id = view_id.lower()

    if default is _sentinel:
        return _VIEWS[view_id].view_path

    v = _VIEWS.get(view_id)
    return v.view_path if v else default


class _View(object):
    view_id = None
    view_name = None
    view_parameters = None
    view_subsection = False
    view_permissions = [ ]
    view_template = None
    view_section = None
    view_order = 10
    view_parent = None
    view_help = None
    view_extensions = []
    view_layout = "BaseView"
    view_require_session = True

    def render(self):
        pass

    def _render(self):
        self.parameters = {}
        if self.view_parameters:
            self.parameters = self.view_parameters(self, env.request.web.arguments)
            self.parameters.normalize(self.view_id, env.request.user)
            self.parameters.handleLists()

        env.request.parameters = self.parameters

        if self.view_template and self.dataset is None:
            self.dataset = template.PrewikkaTemplate(self.view_template)

        if self.dataset is not None:
            _VIEWS["baseview"].setup_dataset(self.dataset)

        for name, classobj in self.view_extensions:
            obj = classobj()
            setattr(self, name, obj)

            obj.render()

    def respond(self):
        env.log.info("Loading view %s" % (self.view_id))

        self._render()
        response = self.render()

        if response and not issubclass(response.__class__, PrewikkaResponse):
            response = PrewikkaResponse(response)

        if not response:
            response = PrewikkaResponse(self.dataset.render() if self.dataset else None)

        if self.dataset:
            for name, clname in self.view_extensions:
                obj = getattr(self, name)
                response.ext_content[name] = obj.dataset.render([self.dataset or {}])

        return response

    def __init__(self):
        self.dataset = None

        if not self.view_id:
            self.view_id = self.__class__.__name__.lower()

        if not self.view_section:
            self.view_section = _("Unknown")

        if self.view_parent:
            self.view_section, self.view_name = self.view_parent.view_section, self.view_parent.view_name

        self.view_path = None

        if self.view_name:
                self.view_path = self.view_section + "/" + self.view_name

        if self.view_parent:
                self.view_path += "/" + self.view_id

        if self.view_path:
                self.view_path = utils.nameToPath(self.view_path)

        _VIEWS[self.view_id] = self

    def __copy__(self):
        ret = self.__class__.__new__(self.__class__)
        ret.__dict__.update(self.__dict__)
        return ret




class View(_View, pluginmanager.PluginBase):
    def __init__(self):
        _View.__init__(self)
        pluginmanager.PluginBase.__init__(self)



class ViewManager:
    def getViewPath(self, view_id, default=_sentinel):
        return getViewPath(view_id, default)

    def getViewID(self, request):
        return self.getViewIDFromPaths(request.path_elements)

    def getViewIDFromPaths(self, paths):
        sections = env.menumanager.get_sections_path()
        view_id = None
        try:
                views = sections.get(paths[0], {}).get(paths[1])
                if not views:
                        return

                view_id = views.keys()[0] if len(paths) == 2 else paths[-1]
        except:
                return paths[-1] if paths else None # View identified solely by ID, like /logout

        return view_id

    def getView(self, view_id):
        return self._views.get(view_id.lower())

    def loadView(self, request, userl):
        view = view_layout = None

        view_id = self.getViewID(request)
        if view_id:
            view = self.getView(view_id)
        else:
            view = next((x for x in hookmanager.trigger("HOOK_VIEW_LOAD", request, userl) if x), None)

        if view:
            view_layout = view.view_layout

        if not request.is_xhr and not request.is_stream and view_layout and not "_download" in request.arguments:
            view = self.getView(view_layout)

        if not view:
            raise InvalidViewError(_("View '%s' does not exist") % request.path)

        if userl and view.view_permissions and not userl.has(view.view_permissions):
            raise usergroup.PermissionDeniedError(view.view_permissions, view.view_id)

        return copy(view)


    def addView(self, view):
        if view.view_name:
            env.menumanager.add_section_info(view)

        env.menumanager.add_section(view.view_section)

        self._views[view.view_id] = view

    def loadViews(self):
        #Import here, because of cyclic dependency
        from baseview import BaseView
        self.addView(BaseView())

        for view_class in sorted(pluginmanager.PluginManager("prewikka.views"), key=operator.attrgetter("view_order")):
                try:
                        vi = view_class()
                except error.PrewikkaUserError as e:
                        logger.warning("%s: plugin loading failed: %s", view_class.__name__, e)
                        continue
                except Exception as e:
                        logger.exception("%s: plugin loading failed: %s", view_class.__name__, e)
                        continue

                self.addView(vi)

    def __init__(self):
        self._views = {}
