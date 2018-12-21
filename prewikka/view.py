# Copyright (C) 2004-2019 CS-SI. All Rights Reserved.
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
from prewikka import compat, csrf, error, hookmanager, log, mainmenu, pluginmanager, registrar, response, template, usergroup, utils

import werkzeug.exceptions
from werkzeug.routing import Map, Rule, BaseConverter

if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins


_SENTINEL = object()
_URL_ADAPTER_CACHE = {}
_ROUTE_OVERRIDE_TYPE = ("make_url", "make_parameters", "check_permissions")
logger = log.get_logger(__name__)


def check_permissions(user, users=([], []), groups=([], []), others=[]):
    if user:
        if user in users[0]:
            return user.has(users[1])

        if groups[0] and set(env.auth.get_member_of(user)) & set(groups[0]):
            return user.has(groups[1])

        if others:
            return user.has(others)

    # If there is no users / groups / others permission defined, then it is considered public and we return True
    # Otherwise, if any kind of permission is defined and there was no match, return False.
    return not(users[0] or groups[0] or others)


def route_override(endpoint, type):
    assert(type in _ROUTE_OVERRIDE_TYPE)

    def decorator(func):
        env.viewmanager._route_override.setdefault(type, {})[endpoint] = func

    return decorator


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

    def __init__(self, view, _save=True, **kwargs):
        dict.__init__(self, **kwargs)

        self.view = view
        self._save = _save
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

    def normalize(self):
        do_update = self._save and env.request.web.method == "PATCH"
        do_save = self._save and env.request.web.method in ("POST", "PUT", "PATCH")

        for name, value in self.items():
            param = self._parameters.get(name)
            if not param:
                if not(self.allow_extra_parameters):
                    raise InvalidParameterError(name)

                continue

            value = param.parse(value)
            if env.request.user and param.save and do_save:
                env.request.user.set_property(name, value, self.view.view_endpoint if not(param.general) else None)

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

            if not param.save or not env.request.user:
                continue

            if param.general:
                save_view = ""
            else:
                save_view = self.view.view_endpoint

            if do_save and not(param.persist) and not do_update:
                env.request.user.del_property(name, view=save_view)

            if name not in env.request.user.configuration.get(save_view, {}):
                continue

            value = env.request.user.get_property(name, view=save_view)
            self._default[name] = value
            self[name] = value

        # In case the view was dynamically added through HOOK_VIEW_LOAD, the hook isn't available
        list(hookmanager.trigger("HOOK_%s_PARAMETERS_NORMALIZE" % self.view.view_endpoint.upper(), self))

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

    def pop(self, key, default=None, type=lambda x: x):
        ret = self.get(key, default, type)
        dict.pop(self, key, None)

        return ret


class GeneralParameters(Parameters):
    def register(self):
        Parameters.register(self)
        mainmenu._register_parameters(self)

    def __init__(self, vobj, kw):
        # Only allow parameters saving if the view is a primary route (has a view_menu entry)
        Parameters.__init__(self, vobj, _save=bool(vobj.view_menu), **kw)
        self.normalize()


class ViewResponse(response.PrewikkaResponse):
    def __init__(self, data, **kwargs):
        response.PrewikkaResponse.__init__(self, {"type": "content", "content": data})

        menu = kwargs.get("menu", mainmenu.HTMLMainMenu() if env.request.has_menu else None)
        if menu:
            self.add_ext_content("menu", menu)

        view_help = env.request.view.view_help
        if view_help:
            if view_help.startswith(("http://", "https://")):
                self.add_ext_content("help", view_help)

            elif env.config.general.get("help_location"):
                self.add_ext_content("help", url_for("baseview.help", path=view_help))


class _ViewDescriptor(object):
    view_parameters = Parameters
    view_template = None
    view_require_session = True
    view_layout = "BaseView.render"
    view_endpoint = None
    view_datatype = None
    view_priority = 0
    view_keywords = set()

    view_help = None
    view_menu = []
    view_permissions = []

    view_users = []
    view_users_permissions = []

    view_groups = []
    view_groups_permissions = []

    view_csrf_exempt = False

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
        if self.view_parameters:
            env.request.parameters = self.view_parameters(self, **env.request.web.arguments)
            env.request.parameters.normalize()

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

    def _criteria_to_urlparams(self, criteria):
        return {}

    def _call_override(self, _type, *args, **kwargs):
        f = env.viewmanager._route_override[_type].get(self.view_endpoint)
        if f:
            return f(self.view_base, *args, **kwargs)

        return getattr(self.view_base, _type)(*args, _view_descriptor=self, **kwargs)

    def make_parameters(self, **kwargs):
        return self._call_override("make_parameters", **kwargs)

    def make_url(self, **kwargs):
        return self._call_override("make_url", **kwargs)

    def check_permissions(self, userl, fail=False, view_kwargs={}):
        ret = self._call_override("check_permissions", userl, view_kwargs=view_kwargs)
        if fail and not ret:
            raise usergroup.PermissionDeniedError(None, env.request.web.path)

        return ret

    def __repr__(self):
        return "_ViewDescriptor(%s)" % self.view_endpoint


class _View(_ViewDescriptor, registrar.DelayedRegistrar):
    view_id = None

    def render(self):
        pass

    def __init__(self):
        if not self.view_id:
            self.view_id = self.__class__.__name__.lower()

        # Avoid initializing DelayedRegistrar twice in case we're a View.
        if not isinstance(self, View):
            registrar.DelayedRegistrar.__init__(self)

        _ViewDescriptor.__init__(self)

    def make_parameters(self, _view_descriptor=None, criteria=None, **kwargs):
        values = {}
        view = _view_descriptor or self

        if criteria:
            kwargs.update(view._criteria_to_urlparams(criteria))

        for k, v in kwargs.items():
            key = "%s[]" % k if isinstance(v, list) else k
            values[key] = v

        return values

    def make_url(self, _view_descriptor=None, **kwargs):
        view = _view_descriptor or self
        return env.viewmanager.url_adapter.build(view.view_endpoint, values=self.make_parameters(**kwargs))

    def check_permissions(self, user, _view_descriptor=None, fail=False, view_kwargs={}):
        view = _view_descriptor or self

        ret = check_permissions(user, (view.view_users, view.view_users_permissions), (view.view_groups, view.view_groups_permissions), view.view_permissions)
        if fail and not ret:
            raise usergroup.PermissionDeniedError(None, env.request.web.path)

        return ret


class View(_View, pluginmanager.PluginBase):
    def __init__(self):
        _View.__init__(self)
        pluginmanager.PluginBase.__init__(self)


def route(path, method=_SENTINEL, methods=["GET"], permissions=[], menu=None, defaults={}, endpoint=None, datatype=None, priority=0, keywords=set(), help=None, parameters=_SENTINEL):
    usergroup.ALL_PERMISSIONS.declare(permissions)

    if method is not _SENTINEL:
        ret = env.viewmanager._add_route(path, method, methods=methods, permissions=permissions, menu=menu,
                                         defaults=defaults, endpoint=endpoint, datatype=datatype, priority=priority,
                                         keywords=keywords, help=help, parameters=parameters)
    else:
        ret = registrar.DelayedRegistrar.make_decorator("route", env.viewmanager._add_route, path, methods=methods, permissions=permissions,
                                                        menu=menu, defaults=defaults, endpoint=endpoint, datatype=datatype, keywords=keywords,
                                                        priority=priority, help=help, parameters=parameters)

    return ret


class ViewManager(registrar.DelayedRegistrar):
    def get(self, datatype=None, keywords=None):
        return sorted(filter(lambda x: set(keywords or []).issubset(x.view_keywords), self._references.get(datatype, [])), key=lambda x: x.view_priority)

    def get_view(self, endpoint, default=None):
        endpoint = endpoint.lower()

        if endpoint[0] == "." and env.request.view:
            endpoint = "%s%s" % (env.request.view.view_id, endpoint)

        return self._views_endpoints.get(endpoint, default)

    def get_view_by_path(self, path, method=None, check_permissions=True):
        try:
            rule, view_kwargs = self.url_adapter.match(path, method=method, return_rule=True)

        except werkzeug.exceptions.MethodNotAllowed:
            raise InvalidMethodError(N_("Method '%(method)s' is not allowed for view '%(view)s'",
                                        {"method": method, "view": path}))

        except werkzeug.exceptions.NotFound:
            raise InvalidViewError(N_("View '%s' does not exist", path))

        if check_permissions and not rule._prewikka_view.check_permissions(env.request.user, view_kwargs=view_kwargs):
            raise usergroup.PermissionDeniedError(rule._prewikka_view.view_permissions, path)

        return rule._prewikka_view, view_kwargs

    def get_baseview(self):
        # Import here, because of cyclic dependency
        from prewikka import baseview

        bview = self.get_view("baseview.render")
        if not bview:
            bview = baseview.BaseView()
            self._generic_add_view(bview, "/views/baseview")

        return bview

    def load_view(self, request, userl):
        view_layout = None

        view, view_kwargs = self.get_view_by_path(request.path, method=request.method)
        if view:
            view_layout = view.view_layout

        if not (request.is_xhr or request.is_stream) and view_layout:
            view = self.get_view(view_layout)

        elif view_kwargs:
            env.request.view_kwargs = view_kwargs

        if not view.view_csrf_exempt:
            csrf.process(request)

        env.request.view = view
        return view

    def _generic_add_view(self, view, path, methods=None, defaults=None):
        rule = Rule(path, endpoint=view.view_endpoint, methods=methods, defaults=defaults)
        rule._prewikka_view = view

        self._views_endpoints[view.view_endpoint] = view
        self._rule_map.add(rule)

    def _add_route(self, path, method=None, methods=["GET"], permissions=[], menu=None, defaults={}, endpoint=None, datatype=None, priority=0, keywords=set(), help=None, parameters=None):
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
        v.view_menu = menu
        v.view_permissions = set(permissions) | set(baseview.view_permissions)
        v.view_endpoint = "%s.%s" % (v.view_id, endpoint or method.__name__)
        v.view_datatype = datatype
        v.view_priority = priority
        v.view_keywords = set(keywords)

        if menu:
            env.menumanager.add_section_info(menu[0], menu[1], v.view_endpoint)

        if datatype:
            self._references.setdefault(datatype, []).append(v)
            v._criteria_to_urlparams = baseview._criteria_to_urlparams

        self._generic_add_view(v, path, methods=methods, defaults=defaults)

    def load_views(self, autoupdate=False):
        self._init()
        self.get_baseview()

        for view_class in pluginmanager.PluginManager("prewikka.views", autoupdate):
            try:
                pluginmanager.PluginManager.initialize_plugin(view_class)
            except Exception:
                continue

    @property
    def url_adapter(self):
        scname = None
        if env.request.web:
            scname = env.request.web.get_script_name()

        ad = _URL_ADAPTER_CACHE.get(scname)
        if not ad:
            ad = _URL_ADAPTER_CACHE[scname] = self._rule_map.bind("", scname)

        return ad

    def _init(self):
        _URL_ADAPTER_CACHE.clear()

        self._references = {}
        self._views_endpoints = {}

        self._route_override = {}
        for i in _ROUTE_OVERRIDE_TYPE:
            self._route_override[i] = {}

        self._rule_map = Map(converters={'list': ListConverter})

    def __init__(self):
        registrar.DelayedRegistrar.__init__(self)
        self._init()

        builtins.url_for = self.url_for

    def url_for(self, endpoint, _default=_SENTINEL, **kwargs):
        view = self.get_view(endpoint=endpoint)
        if not view:
            if _default is not _SENTINEL:
                return _default

            raise InvalidViewError(N_("View '%s' does not exist", endpoint))

        try:
            return view.make_url(**kwargs)
        except Exception as exc:
            if _default is not _SENTINEL:
                return _default

            raise exc
