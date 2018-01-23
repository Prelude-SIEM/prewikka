# Copyright (C) 2004-2018 CS-SI. All Rights Reserved.
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

from copy import copy
from prewikka import compat, error, hookmanager, log, mainmenu, pluginmanager, registrar, response, template, usergroup, utils

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

    def __init__(self, name, type, mandatory=False, default=None, save=False, general=False, persist=False):
        """ Args :
        name : Name of the parameter
        type : Type of the parameter (int, str, list, ...)
        mandatory : True if the parameter is mandatory
        default : Specify a default value
        save : True if the parameter is store in BDD to when set
        general : True if the parameter is available for all the view """

        self.name = name
        self.save = save or persist
        self.persist = persist
        self.general = general
        self.default = default
        self.mandatory = mandatory

        if type is list:
            self.type = [text_type]
        else:
            self.type = type

    def has_default(self):
        """ Return True if this parameter has a default value """
        return self.default is not None

    def _mklist(self, value):
        """ Return the value as a list """

        if not isinstance(value, list):
            return [value]

        return value

    def parse(self, value):
        """ Return the value according to the parameter's type """

        try:
            if isinstance(self.type, list):
                value = [self.type[0](i) for i in self._mklist(value)]
            else:
                value = self.type(value)

        except (ValueError, TypeError):
            raise InvalidParameterValueError(self.name, value)

        return value


class Parameters(dict):
    allow_extra_parameters = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

        self._hard_default = {}
        self._default = {}
        self._parameters = {}

        self.register()

    def register(self):
        pass

    def mandatory(self, name, type):
        self._parameters[name] = ParameterDesc(name, type, mandatory=True, save=True)

    def optional(self, name, type, default=None, save=False, general=False, persist=False):
        if default is not None:
            self._default[name] = self._hard_default[name] = default

        self._parameters[name] = ParameterDesc(name, type, mandatory=False, default=default, save=save, general=general, persist=persist)

    def normalize(self, view, user, save=True):
        do_update = save and env.request.web.method == "PATCH"
        do_save = save and env.request.web.method in ("POST", "PUT", "PATCH")

        for name, value in self.items():
            param = self._parameters.get(name)
            if not param:
                if not(self.allow_extra_parameters):
                    raise InvalidParameterError(name)

                continue

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
                save_view = ""
            else:
                save_view = view

            if do_save and not(param.persist) and not do_update:
                user.del_property(name, view=save_view)

            if name not in user.configuration.get(save_view, {}):
                continue

            value = user.get_property(name, view=save_view)
            self._default[name] = value
            self[name] = value

        # In case the view was dynamically added through HOOK_VIEW_LOAD, the hook isn't available
        list(hookmanager.trigger("HOOK_%s_PARAMETERS_NORMALIZE" % view.upper(), self))

    def handleLists(self, value):
        if isinstance(value, dict):
            if all(key.isdigit() for key in value):
                return [self.handleLists(val) for key, val in sorted(value.items(), key=lambda x: int(x[0]))]

            return dict((key, self.handleLists(val)) for key, val in value.items())

        elif isinstance(value, list):
            return [self.handleLists(val) for val in value]

        return value

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

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            raise MissingParameterError(key)

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

    def get(self, key, default=None, type=lambda x: x):
        ret = dict.get(self, key, default)
        if ret is None:
            return ret

        try:
            if isinstance(ret, list):
                return [type(i) for i in ret]
            else:
                return type(ret)
        except ValueError:
            raise InvalidParameterValueError(key, ret)

    def getlist(self, key, type=lambda x: x):
        ret = self.get(key, default=[], type=type)
        if not isinstance(ret, list):
            raise InvalidParameterValueError(key, ret)

        return ret


class GeneralParameters(Parameters):
    def register(self):
        Parameters.register(self)
        mainmenu._register_parameters(self)

    def __init__(self, vobj, kw):
        Parameters.__init__(self, kw)
        # Only allow parameters saving if the view is a primary route (has a view_menu entry)
        self.normalize(vobj.view_endpoint or vobj.view.view_id, env.request.user, save=bool(vobj.view_menu))


class ViewResponse(response.PrewikkaResponse):
    def __init__(self, data, **kwargs):
        response.PrewikkaResponse.__init__(self, {"type": "view", "content": data})

        menu = kwargs.get("menu", mainmenu.HTMLMainMenu() if env.request.has_menu else None)
        if menu:
            self.add_ext_content("menu", menu)

        if env.request.view.view_help and env.config.general.get("help_location"):
            self.add_ext_content("help", url_for("baseview.help", path=env.request.view.view_help))


class _ViewDescriptor(object):
    view_parameters = Parameters
    view_template = None
    view_require_session = True
    view_layout = "BaseView"
    view_endpoint = None
    view_datatype = None
    view_keywords = set()

    view_help = None
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

    def _setup_dataset_default(self, dataset):
        dataset["document"] = utils.AttrObj()
        dataset["document"].base_url = utils.iri2uri(env.request.web.get_baseurl())
        dataset["document"].href = utils.iri2uri(env.request.web.get_uri())

    def _render(self):
        self.process_parameters()

        if self.view_template:
            env.request.dataset = self.view_template.dataset()

        if env.request.dataset is not None:
            self._setup_dataset_default(env.request.dataset)

        return self.render(**env.request.view_kwargs) or env.request.dataset

    def process_parameters(self):
        env.request.parameters = {}
        if self.view_parameters:
            env.request.parameters = self.view_parameters(env.request.web.arguments)
            env.request.parameters.normalize(self.view_endpoint or self.view_id, env.request.user)

    def respond(self):
        env.log.info("Loading view %s, endpoint %s" % (self.__class__.__name__, self.view_endpoint))

        resp = self._render()

        if isinstance(resp, (template._Dataset, compat.STRING_TYPES)):
            resp = ViewResponse(resp)

        elif not(resp) or not issubclass(resp.__class__, response.PrewikkaResponse):  # Any other type (eg: dict)
            resp = response.PrewikkaResponse(resp)

        if self.view_endpoint:
            list(hookmanager.trigger("HOOK_VIEW_%s_RESPONSE" % self.view_endpoint.upper(), resp))

        if resp.data:
            resp.add_ext_content("_source", self.view_endpoint)

        return resp

    def check_permissions(self, user):
        if user:
            if user in self.view_users:
                return user.has(self.view_users_permissions)

            if self.view_groups and set(env.auth.get_member_of(user)) & self.view_groups:
                return user.has(self.view_groups_permissions)

            if self.view_permissions:
                return user.has(self.view_permissions)

        # If this view has no users / groups / others permission defined, then it is considered public and we return True
        # Otherwise, if any kind of permission is defined and there was no match, return False.
        return not(self.view_users or self.view_groups or self.view_permissions)

    def _criteria_to_urlparams(self, criteria):
        return {}

    def make_url(self, **kwargs):
        return self.view_base.make_url(_view_descriptor=self, **kwargs)


class _View(_ViewDescriptor, registrar.DelayedRegistrar):
    view_id = None
    view_path = None
    view_menu = []

    def render(self):
        pass

    def __init__(self):
        if not self.view_id:
            self.view_id = self.__class__.__name__.lower()

        # Avoid initializing DelayedRegistrar twice in case we're a View.
        if not isinstance(self, View):
            registrar.DelayedRegistrar.__init__(self)

        _ViewDescriptor.__init__(self)

        if self.view_template and not isinstance(self.view_template, template.PrewikkaTemplate):
            self.view_template = template.PrewikkaTemplate(self.view_template)

        if not self.view_path:
            if self.view_menu:
                self.view_path = "/" + "/".join(self.view_menu)

            if self.view_path:
                self.view_path = utils.nameToPath(self.view_path)

    def make_parameters(self, criteria=None, **kwargs):
        values = {}

        if criteria:
            kwargs.update(self._criteria_to_urlparams(criteria))

        for k, v in kwargs.items():
            key = "%s[]" % k if isinstance(v, list) else k
            values[key] = v

        return values

    def make_url(self, _view_descriptor=None, **kwargs):
        if _view_descriptor:
            endpoint = _view_descriptor.view_endpoint
        else:
            endpoint = self.view_endpoint

        return env.request.url_adapter.build(endpoint, values=self.make_parameters(**kwargs))


class View(_View, pluginmanager.PluginBase):
    def __init__(self):
        _View.__init__(self)
        pluginmanager.PluginBase.__init__(self)


def route(path, method=_SENTINEL, methods=["GET"], permissions=[], menu=None, defaults={}, endpoint=None, datatype=None, keywords=set(), help=None, parameters=_SENTINEL):
    usergroup.ALL_PERMISSIONS.declare(permissions)

    if method is not _SENTINEL:
        ret = env.viewmanager._add_route(path, method, methods=methods, permissions=permissions, menu=menu,
                                         defaults=defaults, endpoint=endpoint, datatype=datatype, keywords=keywords, help=help, parameters=parameters)
    else:
        ret = registrar.DelayedRegistrar.make_decorator("route", env.viewmanager._add_route, path, methods=methods, permissions=permissions,
                                                        menu=menu, defaults=defaults, endpoint=endpoint, datatype=datatype, keywords=keywords, help=help, parameters=parameters)

    return ret


class ViewManager(registrar.DelayedRegistrar):
    def get(self, datatype=None, keywords=None):
        return filter(lambda x: set(keywords or []).issubset(x.view_keywords), self._references.get(datatype, []))

    def getView(self, id=None, endpoint=None):
        if id:
            return self._views.get(id.lower())

        endpoint = endpoint.lower()

        if endpoint[0] == "." and env.request.view:
            endpoint = "%s%s" % (env.request.view.view_id, endpoint if len(endpoint) > 1 else "")

        if endpoint[0] != "." and endpoint.find(".") == -1:
            endpoint += ".render"

        return self._views_endpoints[endpoint]

    def _getViewByPath(self, path, method=None):
        try:
            rule, view_kwargs = env.request.url_adapter.match(path, method=method, return_rule=True)

        except werkzeug.exceptions.MethodNotAllowed:
            raise InvalidMethodError(N_("Method '%(method)s' is not allowed for view '%(view)s'",
                                        {"method": method, "view": path}))

        except werkzeug.exceptions.NotFound:
            raise InvalidViewError(N_("View '%s' does not exist", path))

        return rule._prewikka_view, view_kwargs

    def getViewByPath(self, path, method=None):
        return self._getViewByPath(path, method)[0]

    def loadView(self, request, userl):
        view_layout = None

        view, view_kwargs = self._getViewByPath(request.path, method=request.method)
        if view:
            view_layout = view.view_layout

        if not (request.is_xhr or request.is_stream) and view_layout:
            view = self._views.get(view_layout.lower())

        elif view_kwargs:
            env.request.view_kwargs = view_kwargs

        if not view:
            raise InvalidViewError(N_("View '%s' does not exist", request.path))

        if not view.check_permissions(userl):
            raise usergroup.PermissionDeniedError(view.view_permissions, request.path)

        env.request.view = view
        return view

    def _add_route(self, path, method=None, methods=["GET"], permissions=[], menu=None, defaults={}, endpoint=None, datatype=None, keywords=set(), help=None, parameters=None):
        baseview = method.__self__

        v = _ViewDescriptor()
        v.render = method
        v.view_base = baseview
        v.view_id = baseview.view_id
        v.view_template = baseview.view_template
        v.view_users = baseview.view_users
        v.view_groups = baseview.view_groups
        v.view_layout = baseview.view_layout
        v.view_require_session = baseview.view_require_session

        if parameters is _SENTINEL:
            v.view_parameters = baseview.view_parameters
        else:
            v.view_parameters = parameters

        v.view_help = help or baseview.view_help
        v.view_path = path[1:]
        v.view_menu = menu or baseview.view_menu
        v.view_permissions = set(permissions) | set(baseview.view_permissions)
        v.view_endpoint = "%s.%s" % (v.view_id, endpoint or method.__name__)
        v.view_datatype = datatype
        v.view_keywords = set(keywords)

        if v.view_menu:
            env.menumanager.add_section_info(v)

        if datatype:
            self._references.setdefault(datatype, []).append(v)
            v._criteria_to_urlparams = baseview._criteria_to_urlparams

        rule = Rule(path, endpoint=v.view_endpoint, methods=methods, defaults=defaults)
        rule._prewikka_view = v

        self._rule_map.add(rule)
        self._views_endpoints[v.view_endpoint] = v

    def addView(self, view):
        rdfunc = getattr(view, "render")
        route = getattr(rdfunc, registrar._ATTRIBUTE, {}).get("route")

        if rdfunc and not route:
            if not view.view_path:
                view.view_path = "/views/%s" % (view.view_id)

            if view.view_menu:
                env.menumanager.add_section_info(view)

            view.view_endpoint = "%s.render" % (view.view_id)

            if view.view_datatype:
                self._references.setdefault(view.view_datatype, []).append(view)

            rule = Rule((view.view_path or "/" + view.view_id), endpoint=view.view_endpoint)
            rule._prewikka_view = view

            self._rule_map.add(rule)

            self._views[view.view_id] = view
            self._views_endpoints[view.view_endpoint] = view

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
        scname = request.web.get_script_name() if request.web else None

        ad = _URL_ADAPTER_CACHE.get(scname) if cache else None
        if not ad:
            ad = _URL_ADAPTER_CACHE[scname] = self._rule_map.bind("", scname)

        request.url_adapter = ad

    def __init__(self):
        registrar.DelayedRegistrar.__init__(self)

        self._views = {}
        self._routes = Map()
        self._references = {}
        self._views_endpoints = {}

        self._rule_map = Map(converters={'list': ListConverter})

        builtins.url_for = self.url_for

    def url_for(self, endpoint, _default=_SENTINEL, **kwargs):
        try:
            return self.getView(endpoint=endpoint).make_url(**kwargs)
        except Exception as exc:
            if _default is not _SENTINEL:
                return _default

            raise exc

    def __contains__(self, view_id):
        return view_id in self._views
