# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import operator

from copy import copy
from prewikka import database, env, error, hookmanager, log, pluginmanager, template, usergroup, utils
from prewikka.response import PrewikkaResponse

import werkzeug.exceptions
from werkzeug.routing import Map, Rule, BaseConverter

if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins


_SENTINEL = object()
_URL_ADAPTER_CACHE = {}
logger = log.getLogger(__name__)


class ParameterError(Exception):
        pass


class InvalidParameterError(error.PrewikkaUserError):
    def __init__(self, name):
        error.PrewikkaUserError.__init__(self, N_("Parameters Normalization failed"),
                                         N_("Parameter '%s' is not valid", name),
                                         log_priority=log.WARNING)


class InvalidParameterValueError(error.PrewikkaUserError):
    def __init__(self, name, value):
        error.PrewikkaUserError.__init__(self, N_("Parameters Normalization failed"),
                                         N_("Invalid value '%(value)s' for parameter '%(name)s'", {'value': value, 'name': name}),
                                         log_priority=log.WARNING)


class MissingParameterError(error.PrewikkaUserError):
    def __init__(self, name):
        error.PrewikkaUserError.__init__(self, N_("Parameters Normalization failed"),
                                         N_("Required parameter '%s' is missing", name),
                                         log_priority=log.WARNING)


class InvalidMethodError(error.PrewikkaUserError):
    def __init__(self, message, log_priority=None, **kwargs):
        error.PrewikkaUserError.__init__(self, N_("Invalid method"), message, log_priority=log.ERROR, **kwargs)


class InvalidViewError(error.PrewikkaUserError):
    code = 404

    def __init__(self, message, log_priority=None, **kwargs):
        error.PrewikkaUserError.__init__(self, N_("Invalid view"), message, log_priority=log.ERROR, **kwargs)


class ListConverter(BaseConverter):
    def to_python(self, value):
        return value.split(',')

    def to_url(self, values):
        return ','.join(BaseConverter.to_url(self, value) for value in values)


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
            self.type = [ text_type ]
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
                value = [ self.type[0](i) for i in self._mklist(value) ]
            else:
                value = self.type(value)

        except (ValueError, TypeError):
            raise InvalidParameterValueError(self.name, value)

        return value


class Parameters(dict):
    allow_extra_parameters = True

    def __init__(self, view, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        self._hard_default = {}
        self._default = {}
        self._parameters = {}

        self.register()
        self.optional("_save", text_type)
        self.optional("_download", text_type)

        list(hookmanager.trigger("HOOK_%s_PARAMETERS_REGISTER" % view.view_id.upper(), self))

    def register(self):
        pass

    def mandatory(self, name, type):
        self._parameters[name] = ParameterDesc(name, type, mandatory=True, save=True)

    def optional(self, name, type, default=None, save=False, general=False):
        if default is not None:
            self._default[name] = self._hard_default[name] = default

        self._parameters[name] = ParameterDesc(name, type, mandatory=False, default=default, save=save, general=general)

    @database.use_transaction
    def process(self, view_id):
        # In the future, the following should be handled directly in normalize()
        if env.request.user:
            env.request.user.begin_properties_change()

        self.normalize(view_id, env.request.user)
        self.handleLists()

        if env.request.user:
            env.request.user.commit_properties_change()

    def normalize(self, view, user):
        do_load = True
        do_save = "_save" in self

        for name, value in self.items():
            param = self._parameters.get(name)
            if not param:
                if not(self.allow_extra_parameters):
                    raise InvalidParameterError(name)

                continue

            if name not in self._parameters or param.mandatory is False:
                do_load = False

            value = param.parse(value)
            if user and param.save and do_save:
                user.set_property(name, value, view if not(param.general) else None)

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
        obj_list = []
        obj_dict = {}
        obj_order = []
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
                obj_dict[order] = {} if has_value else []
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
        if param not in self._parameters:
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
            return param in self._hard_default
        else:
            return param in self._default

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

    def getlist(self, key):
        ret = self.get(key, [])
        if not ret:
            return ret

        if not isinstance(ret, list):
            ret = [ ret ]

        return ret



class _ViewDescriptor(object):
    view_parameters = Parameters
    view_template = None
    view_require_session = True
    view_extensions = []
    view_layout = "BaseView"
    view_endpoint = None

    view_permissions = []

    view_users = []
    view_users_permissions = []

    view_groups = []
    view_groups_permissions = []

    @property
    def view_others_permissions(self):
        return self.view_permissions

    @view_others_permissions.setter
    def view_others_permissions(self, permissions):
        self.view_permissions = permissions

    def __init__(self):
        self.view_users = set(self.view_users)
        self.view_groups = set(self.view_groups)

    def _setup_dataset_default(self):
        env.request.dataset["document"] = utils.AttrObj()
        env.request.dataset["document"].base_url = env.request.web.get_baseurl()
        env.request.dataset["document"].href = env.request.web.get_uri()

    def _render(self, dataset):
        env.request.parameters = {}
        if self.view_parameters:
            env.request.parameters = self.view_parameters(self, env.request.web.arguments)
            env.request.parameters.process(self.view_id)

        if self.view_template and dataset is None:
            env.request.dataset = self.view_template.dataset()
        else:
            env.request.dataset = dataset

        if env.request.dataset is not None:
            self._setup_dataset_default()

        for name, classobj in self.view_extensions:
            obj = classobj()
            setattr(env.request, name, obj)

            obj.render()

        return env.request.dataset

    def respond(self, dataset=None, code=None):
        env.log.info("Loading view %s, endpoint %s" % (self.__class__.__name__, self.view_endpoint))

        dataset = self._render(dataset)
        response = self.render(**env.request.view_kwargs)

        if response and not issubclass(response.__class__, PrewikkaResponse):
            response = PrewikkaResponse(response, code=code)

        if not response:
            response = PrewikkaResponse(dataset.render() if dataset else None, code=code)

        for name, clname in self.view_extensions:
            response.add_ext_content(name, getattr(env.request, name).dataset.render())

        return response

    def check_permissions(self, user):
        if user:
            if user in self.view_users:
                return user.has(self.view_users_permissions)

            if self.view_groups and set(env.auth.getMemberOf(user)) & self.view_groups:
                return user.has(self.view_groups_permissions)

            if self.view_permissions:
                return user.has(self.view_permissions)

        # If this view has no users / groups / others permission defined, then it is considered public and we return True
        # Otherwise, if any kind of permission is defined and there was no match, return False.
        return not(self.view_users or self.view_groups or self.view_permissions)


class _View(_ViewDescriptor):
    view_id = None
    view_path = None
    view_menu = []

    def render(self):
        pass

    def __init__(self):
        _ViewDescriptor.__init__(self)

        if self.view_template and not isinstance(self.view_template, template.PrewikkaTemplate):
            self.view_template = template.PrewikkaTemplate(self.view_template)

        if not self.view_id:
            self.view_id = self.__class__.__name__.lower()

        if not self.view_path:
            if self.view_menu:
                self.view_path = "/" + "/".join(self.view_menu)

            if self.view_path:
                self.view_path = utils.nameToPath(self.view_path)


class View(_View, pluginmanager.PluginBase):
    def __init__(self):
        _View.__init__(self)
        pluginmanager.PluginBase.__init__(self)


class _Route(object):
    def __init__(self, path, methods=["GET"], permissions=[], menu=None):
        self.permissions = permissions
        self.path = path
        self.methods = methods
        self.menu = menu


def route(route, methods=["GET"], permissions=[], menu=None):
    usergroup.ALL_PERMISSIONS.declare(permissions)

    def decorator(func):
        r = getattr(func, "__prewikka_route__", None)
        if not r:
            func.__prewikka_route__ = []

        func.__prewikka_route__.append(_Route(route, methods, permissions, menu))
        return func

    return decorator


class ViewManager(object):
    def getView(self, view_id):
        return self._views.get(view_id.lower())

    def loadView(self, request, userl):
        view = view_kwargs = view_layout = None

        try:
            endpoint, view_kwargs = env.request.url_adapter.match(request.path, method=request.method)
            view = self._views_endpoint[endpoint]

        except werkzeug.exceptions.MethodNotAllowed:
            raise InvalidMethodError(N_("Method '%(method)s' is not allowed for view '%(view)s'",
                                        {"method": request.method, "view": request.path}))

        except werkzeug.exceptions.NotFound:
            raise InvalidViewError(N_("View '%s' does not exist", request.path))

        if view:
            view_layout = view.view_layout

        if not request.is_xhr and not request.is_stream and view_layout and "_download" not in request.arguments:
            view = self._views.get(view_layout.lower())

        elif view_kwargs:
            env.request.view_kwargs = view_kwargs

        if not view:
            raise InvalidViewError(N_("View '%s' does not exist", request.path))

        if not view.check_permissions(userl):
            raise usergroup.PermissionDeniedError(view.view_permissions, request.path)

        env.request.view = view
        return view

    def _route2viewdesc(self, baseview, function, route):
        v = _ViewDescriptor()

        v.view_template = baseview.view_template
        v.view_users = baseview.view_users
        v.view_groups = baseview.view_groups
        v.view_permissions = set(route.permissions) | set(baseview.view_permissions)

        v.view_id = baseview.view_id
        v.view_path = route.path[1:]
        v.view_require_session = baseview.view_require_session
        v.view_layout = baseview.view_layout
        v.view_extensions = baseview.view_extensions
        v.view_parameters = baseview.view_parameters
        v.view_menu = route.menu or baseview.view_menu
        v.view_endpoint = "%s.%s" % (baseview.view_id, function.__name__)
        v.render = function

        if v.view_menu:
            env.menumanager.add_section_info(v)

        return v

    def addView(self, view):
        for name in dir(view):
            if isinstance(getattr(type(view), name, None), property):
                continue

            ref = getattr(view, name)
            for route in getattr(ref, "__prewikka_route__", []):
                vd = self._route2viewdesc(view, ref, route)

                self._views_endpoint[vd.view_endpoint] = vd
                self._rule_map.add(Rule(route.path, methods=route.methods, endpoint=vd.view_endpoint))

        rdfunc = getattr(view, "render")
        if rdfunc and not getattr(rdfunc, "__prewikka_route__", []):
            if not view.view_path:
                view.view_path = "/views/%s" % (view.view_id)

            if view.view_menu:
                env.menumanager.add_section_info(view)

            view.view_endpoint = "%s.render" % (view.view_id)

            self._views_endpoint[view.view_endpoint] = view
            self._rule_map.add(Rule((view.view_path or "/" + view.view_id), endpoint=view.view_endpoint))
            self._views[view.view_id] = view

    def loadViews(self):
        # Import here, because of cyclic dependency
        from prewikka.baseview import BaseView
        self.addView(BaseView())

        for view_class in pluginmanager.PluginManager("prewikka.views"):
            try:
                vi = view_class()
            except error.PrewikkaUserError as e:
                logger.warning("%s: plugin loading failed: %s", view_class.__name__, e)
                continue
            except Exception as e:
                logger.exception("%s: plugin loading failed: %s", view_class.__name__, e)
                continue

            self.addView(vi)

    def set_url_adapter(self, request, cache=True):
        scname = request.web.get_script_name()

        ad = _URL_ADAPTER_CACHE.get(scname) if cache else None
        if not ad:
            ad = _URL_ADAPTER_CACHE[scname] = self._rule_map.bind("", scname)

        request.url_adapter = ad

    def __init__(self):
        self._views = {}
        self._routes = Map()

        self._views_endpoint = {}
        self._rule_map = Map(converters={'list': ListConverter})

        builtins.url_for = self.url_for

    def url_for(self, endpoint, **kwargs):
        endpoint = endpoint.lower()

        if endpoint[0] == "." and env.request.view:
            endpoint = "%s%s" % (env.request.view.view_id, endpoint if len(endpoint) > 1 else "")

        if endpoint[0] != "." and endpoint.find(".") == -1:
            endpoint += ".render"

        default = kwargs.pop("_default", _SENTINEL)
        if default is not _SENTINEL and endpoint not in self._views_endpoint:
            return default

        return env.request.url_adapter.build(endpoint, values=kwargs)

    def __contains__(self, view_id):
        return view_id in self._views
