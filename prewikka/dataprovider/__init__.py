# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
# Author: Abdel Elmili <abdel.elmili@c-s.fr>
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

import copy
import time
from datetime import datetime

from prewikka import compat, error, hookmanager, pluginmanager
from prewikka.utils import AttrObj, CachingIterator, json
from prewikka.utils.timeutil import parser, tzutc


def PathInfo(path, value_type, operators=[], value_accept=[], type=None):
    assert(operators or type)

    if not operators:
        backend = env.dataprovider._backends[type]
        operators = backend.TYPE_OPERATOR_MAPPING.get(value_type, backend.TYPE_OPERATOR_MAPPING.get(None, []))

    return AttrObj(path=path, field=".".join(path.split(".")[1:]), type=value_type, operators=operators, value_accept=value_accept)


def _str_to_datetime(date):
    if date.isdigit():
        return datetime.utcfromtimestamp(int(date))

    return parser.parse(date)


_DATETIME_CONVERTERS = {
    int: datetime.utcfromtimestamp,
    float: datetime.utcfromtimestamp,
    text_type: _str_to_datetime,
    datetime: lambda x: x,
    type(None): lambda x: x
}

_sentinel = object()


def to_datetime(date):
    try:
        dt = _DATETIME_CONVERTERS[type(date)](date)
    except KeyError:
        raise error.PrewikkaUserError(N_("Conversion error"),
                                      N_("Value %(value)r cannot be converted to %(type)s",
                                         {"value": date, "type": "datetime"}))
    if dt is not None and dt.tzinfo is None:
        # Make the datetime timezone-aware
        return dt.replace(tzinfo=tzutc())

    return dt


class DataProviderError(Exception):
    pass


class NoBackendError(DataProviderError):
    pass


class ItemNotFoundError(error.PrewikkaUserError):
    pass


class QueryResultsRow(CachingIterator):
    __slots__ = ("_parent")

    def __init__(self, parent, items):
        CachingIterator.__init__(self, items)
        self._parent = parent

    def _get_current_path_type(self):
        return self._parent._paths_types[len(self._cache)]

    def _get_current_path(self):
        return self._parent._paths[len(self._cache)]

    def _cast(self, value):
        type = self._get_current_path_type()
        try:
            if type is datetime:
                return to_datetime(value)

            elif type is object:
                return value

            return type(value)
        except (KeyError, ValueError):
            raise error.PrewikkaUserError(N_("Conversion error"),
                                          N_("Value %(value)r cannot be converted to %(type)s", {"value": value, "type": type}))

    def preprocess_value(self, value):
        if value is None:
            return None

        if self._parent._paths_types:
            value = self._cast(value)

        cont = [self._get_current_path(), value]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_READ", cont))

        return cont[1]


class QueryResults(CachingIterator):
    __slots__ = ("_paths", "_paths_types", "duration")

    def preprocess_value(self, value):
        return QueryResultsRow(self, value)


class ResultObject(object):
    def __init__(self, obj, curpath=None):
        self._obj = obj
        self._curpath = curpath or []

    def preprocess_value(self, value):
        return value

    @property
    def path(self):
        return ".".join(self._curpath)

    def _wrapobj(self, obj, curpath):
        if isinstance(obj, type(self._obj)):
            return ResultObject(obj, curpath)

        elif isinstance(obj, tuple):
            return CachingIterator((self._wrapobj(v, curpath[:-1] + ["%s(%d)" % (curpath[-1], i)]) for i, v in enumerate(obj)))

        return obj

    def get(self, key, default=None):
        value = self._obj.get(key)
        if value is None:
            return default

        curpath = self._curpath + [key]

        cont = [".".join(curpath), self.preprocess_value(value)]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_READ", cont))

        return self._wrapobj(cont[1], curpath)

    def __getattr__(self, x):
        return self.__dict__.get(x, getattr(self._obj, x))

    def __getitem__(self, key, default=None):
        return self.get(key, default)


class DataProviderBackend(pluginmanager.PluginBase):
    type = None
    TYPE_OPERATOR_MAPPING = {}

    def post_load(self):
        pass

    def get_values(self, paths, criteria, distinct, limit, offset):
        """
        Retrieves data corresponding to the given paths. If criteria are given,
        only values matching these criteria will be retrieved.

        @param paths: Selected paths
        @type paths: list
        @param criteria: Search criteria
        @type criteria: list
        @param distinct: Control whether duplicate entries should be removed (True) or kept (False)
        @type distinct: int
        @param limit: Maximum number of rows to retrieve. Note: the actual result may contain fewer entries
        @type limit: int
        @param offset: Number of entries to skip before retrieving matching rows
        @type offset: int
        @return: A result set containing the values matching the various criteria
        @rtype QueryResults
        """
        raise error.NotImplementedError

    def get_by_id(self, id_):
        """Retrieve a root object by its ID."""
        raise error.NotImplementedError

    def get(self, criteria, order_by, limit, offset):
        """Retrieve root objects matching the given criteria."""
        raise error.NotImplementedError

    def delete(self, criteria, paths):
        """Delete objects (or, if a root path is given, subobjects) matching the given criteria."""
        raise error.NotImplementedError

    def insert(self, data, criteria):
        """Insert a root object, or, if criteria are given, a subobject."""
        raise error.NotImplementedError

    def update(self, data, criteria):
        """Update root objects matching the given criteria."""
        raise error.NotImplementedError

    def get_path_info(self, path):
        return PathInfo(path, env.dataprovider.get_path_type(path), value_accept=self._get_path_values(path), type=self.type)

    def _get_path_values(self, path):
        return None


class DataProviderBase(pluginmanager.PluginBase):
    dataprovider_type = None
    dataprovider_label = None

    def __init__(self, time_field=None):
        if time_field is None:
            raise error.PrewikkaUserError(N_("Backend normalization error"), N_("Backend normalization error"))

        pluginmanager.PluginBase.__init__(self)
        self._time_field = time_field

    def post_load(self):
        pass

    def get_common_paths(self, index=False):
        return []

    @staticmethod
    def _value_escape(value):
        if isinstance(value, (int, long)):
            return value

        if not isinstance(value, compat.STRING_TYPES):
            value = text_type(value)

        return "'%s'" % value.replace("\\", "\\\\").replace("'", "\\'")

    def format_path(self, path):
        return path.format(backend=self.dataprovider_type, time_field=self._time_field)

    def format_paths(self, paths):
        return [self.format_path(path) for path in paths]

    def parse_paths(self, paths):
        """
        Parse paths and turn them into a structure that can be used by the backend.

        @param paths: List of paths in natural syntax (eg. ["foo.bar", "count(foo.id)"])
        @type paths: list
        @param type: type of backend
        @type type: string
        @return: The paths as a structure that can easily be used by the backend.
        """
        return paths, []

    def compile_criterion(self, criterion):
        return criterion

    def compile_criteria(self, criteria):
        return criteria

    def criterion_to_string(self, path, operator, value):
        if operator == "==" and value is None:
            return "!%s" % (path)

        if operator in ("!=", None) and value is None:
            return path

        return "%s %s %s" % (path, operator, self._value_escape(value))

    def get_paths(self):
        raise error.NotImplementedError

    def get_path_type(self, path):
        raise error.NotImplementedError

    def register_path(self, path, type):
        raise error.NotImplementedError


class Criterion(json.JSONObject):
    def _init(self, left, operator, right):
        self.left, self.operator, self.right = left, operator, right

    def __init__(self, left=None, operator=None, right=None):
        json.JSONObject.__init__(self)

        # Normalize equality test
        if operator == "=":
            operator = "=="

        self._init(left, operator, right)

    def get_paths(self):
        if self.operator in ("&&", "||"):
            return self.left.get_paths() | self.right.get_paths()

        res = set()
        if self.left:
            res.add(self.left)

        return res

    def _compile(self, base):
        if not self.left:
            return copy.copy(self)

        if self.operator in ("&&", "||"):
            return Criterion(self.left._compile(base), self.operator, self.right._compile(base))

        tpl = [base.format_path(self.left), self.right]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_WRITE", tpl))

        return base.compile_criterion(Criterion(tpl[0], self.operator, tpl[1]))

    def to_string(self, type=None):
        if not self.left:
            return ""

        if self.operator in ("&&", "||"):
            return "(" + " ".join((self.left.to_string(type), self.operator, self.right.to_string(type))) + ")"

        if not type:
            return " ".join(text_type(i) for i in [self.left, self.operator, self.right])

        base = env.dataprovider._type_handlers[type]
        return base.criterion_to_string(base.format_path(self.left), self.operator, self.right)

    def to_list(self, type=None):
        if not self.left:
            return []

        if self.operator in ("&&", "||"):
            return self.left.to_list(type) + self.right.to_list(type)
        else:
            return [self]

    def compile(self, type):
        self = copy.copy(self)

        for c in filter(None, hookmanager.trigger("HOOK_DATAPROVIDER_CRITERIA_PREPARE", type)):
            self += c

        base = env.dataprovider._type_handlers[type]
        return base.compile_criteria(self._compile(base))

    def _apply_self(self, operator, other):
        if not other:
            return self

        if self:
            self._init(copy.copy(self), operator, other)
        else:
            self._init(other.left, other.operator, other.right)

        return self

    def _apply_new(self, operator, other):
        if not other:
            return self

        elif not self:
            return other

        return Criterion(self, operator, other)

    def __str__(self):
        return self.to_string()

    def __bool__(self):
        return self.left is not None

    def __copy__(self):
        return Criterion(self.left, self.operator, self.right)

    def __json__(self):
        return {"left": self.left, "operator": self.operator, "right": self.right}

    def __iadd__(self, other):
        return self._apply_self("&&", other)

    def __ior__(self, other):
        return self._apply_self("||", other)

    def __iand__(self, other):
        return self._apply_self("&&", other)

    def __add__(self, other):
        return self._apply_new("&&", other)

    def __or__(self, other):
        return self._apply_new("||", other)

    __and__ = __add__
    __nonzero__ = __bool__


class DataProviderManager(pluginmanager.PluginManager):
    def __init__(self):
        pluginmanager.PluginManager.__init__(self, "prewikka.dataprovider.type")

        self._type_handlers = {}
        self._backends = {}

    def load(self):
        for k in self.keys():
            try:
                p = self[k]()
                p.dataprovider_type = k
            except error.PrewikkaUserError as err:
                env.log.warning("%s: plugin failed to load: %s" % (self[k].__name__, err))
                continue

            self._type_handlers[k] = p

        for plugin in pluginmanager.PluginManager("prewikka.dataprovider.backend"):

            if plugin.type not in self._type_handlers:
                env.log.warning("%s: plugin failed to load: %s" % (plugin.__name__,
                                _("No handler configured for '%s' datatype" % plugin.type)))
                continue

            try:
                p = plugin()
            except error.PrewikkaUserError as err:
                env.log.warning("%s: plugin failed to load: %s" % (plugin.__name__, err))
                continue

            if p.type in self._backends:
                raise error.PrewikkaUserError(N_("Configuration error"),
                                              N_("Only one manager should be configured for '%s' backend", p.type))

            self._backends[p.type] = p

        for p in self._type_handlers.values():
            p.post_load()

        for p in self._backends.values():
            p.post_load()

    @staticmethod
    def _parse_path(path):
        tmp = path.partition('.')
        if not tmp[1]:
            return

        tmp = tmp[0].rpartition('(')[2]
        # Exclude generic paths, eg. "{backend}.{time_field}".
        if tmp != '{backend}':
            return tmp

    def guess_datatype(self, paths, criteria=Criterion(), default=_sentinel):
        res = set()

        for path in set(paths) | criteria.get_paths():
            path = self._parse_path(path)
            if path:
                res.add(path)

        if len(res) != 1:
            if default is not _sentinel:
                return default

            raise DataProviderError("Unable to guess data type: incompatible paths")

        return list(res)[0]

    def _check_data_type(self, type, *args):
        if not type:
            type = self.guess_datatype(*args)

        if type not in self._type_handlers or type not in self._backends:
            raise NoBackendError("No backend available for '%s' datatype" % type)

        return type

    def _normalize(self, type, paths=None, criteria=None):
        if paths is None:
            paths = []

        if criteria is None:
            criteria = Criterion()

        type = self._check_data_type(type, paths, criteria)

        parsed_paths = paths
        paths_types = []

        plugin = self._type_handlers[type]

        paths = plugin.format_paths(paths)
        parsed_paths, paths_types = plugin.parse_paths(paths)

        return AttrObj(type=type, paths=paths, parsed_paths=parsed_paths, paths_types=paths_types, criteria=criteria.compile(type))

    def query(self, paths, criteria=None, distinct=0, limit=-1, offset=0, type=None, **kwargs):
        o = self._normalize(type, paths, criteria)

        start = time.time()
        results = self._backends[o.type].get_values(o.parsed_paths, o.criteria, distinct, limit, offset, **kwargs)
        results.duration = time.time() - start

        results._paths = o.paths
        results._paths_types = o.paths_types

        return results

    def get_by_id(self, type, id_):
        return self._backends[type].get_by_id(id_)

    def get(self, criteria=None, order_by="time_desc", limit=-1, offset=0, type=None):
        if order_by not in ("time_asc", "time_desc"):
            raise DataProviderError("Invalid value for parameter 'order_by'")

        o = self._normalize(type, criteria=criteria)
        return self._backends[o.type].get(o.criteria, order_by, limit, offset)

    def delete(self, criteria=None, paths=None, type=None):
        o = self._normalize(type, paths, criteria)
        return self._backends[o.type].delete(o.criteria, o.parsed_paths)

    @staticmethod
    def _resolve_values(paths, values):
        for tpl in zip(paths, values):
            tpl = list(tpl)
            list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_WRITE", tpl))
            yield tpl

    def insert(self, data, criteria=None, type=None):
        paths = data.keys()
        o = self._normalize(type, paths, criteria)
        return self._backends[o.type].insert(self._resolve_values(o.parsed_paths, data.values()), o.criteria)

    def update(self, data, criteria=None, type=None):
        paths = data.keys()
        o = self._normalize(type, paths, criteria)
        return self._backends[o.type].update(self._resolve_values(o.parsed_paths, data.values()), o.criteria)

    def get_types(self):
        return self._backends.keys()

    def has_type(self, wanted_type):
        return wanted_type in self._backends

    def get_label(self, type):
        return self._type_handlers[type].dataprovider_label

    def register_path(self, path, path_type, type=None):
        if not type:
            type = self.guess_datatype([path])

        return self._type_handlers[type].register_path(path, path_type)

    def get_paths(self, type):
        return self._type_handlers[type].get_paths()

    def get_common_paths(self, type, index=False):
        return self._type_handlers[type].get_common_paths(index)

    def get_path_info(self, path, type=None):
        type = self._check_data_type(type, [path])
        return self._backends[type].get_path_info(path)

    def get_path_type(self, path, type=None):
        type = self._check_data_type(type, [path])
        return self._type_handlers[type].get_path_type(path)
