# Copyright (C) 2016 CS-SI. All Rights Reserved.
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

import copy, types, time
from datetime import datetime

from prewikka import pluginmanager, error, utils, hookmanager
from prewikka.utils.timeutil import parser
from prewikka.utils import CachingIterator, json, compat


def _str_to_datetime(date):
    if date.isdigit():
        return datetime.utcfromtimestamp(int(date))

    return parser.parse(date)

CONVERTERS = {
    int: datetime.utcfromtimestamp,
    float: datetime.utcfromtimestamp,
    str: _str_to_datetime,
    datetime: lambda x:x,
    types.NoneType: lambda x:x
}

def to_datetime(date):
    try:
        return CONVERTERS[type(date)](date)
    except KeyError:
        raise error.PrewikkaUserError(_("Conversion error"),
                                      N_("Value %(value)r cannot be converted to %(type)s",
                                         {"value": date, "type": "datetime"}))
TYPES_FUNC_MAP = {
    "int": int,
    "float": float,
    "long": long,
    "datetime": to_datetime,
    "str": str
}


class DataProviderError(Exception):
    pass


class NoBackendError(DataProviderError):
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
            return TYPES_FUNC_MAP[type](value)
        except (KeyError, ValueError):
            raise error.PrewikkaUserError(_("Conversion error"),
                                          N_("Value %(value)r cannot be converted to %(type)s", {"value": value, "type": type}))

    def preprocess_value(self, value):
        if value is None:
            return None

        if self._parent._paths_types:
            value = self._cast(value)

        cont = [self._get_current_path(), value]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE", cont))

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

    def _wrapobj(self, obj, curpath):
        if type(obj) == type(self._obj):
            return ResultObject(obj, curpath)

        elif isinstance(obj, tuple):
            return CachingIterator((self._wrapobj(i, curpath) for i in obj))

        return obj

    def get(self, key, default=None):
        value = self._obj.get(key)
        if value is None:
            return default

        curpath = self._curpath + [key]

        cont = [ ".".join(curpath), self.preprocess_value(value) ]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE", cont))

        return self._wrapobj(cont[1], curpath)

    def __getattr__(self, x):
        return self.__dict__.get(x, getattr(self._obj, x))

    def __getitem__(self, key, default=None):
        return self.get(key, default)


class DataProviderBackend(pluginmanager.PluginBase):
    type = None

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
        pass


class DataProviderNormalizer(object):
    def __init__(self, time_field=None):
        if time_field is None:
            raise error.PrewikkaUserError(_("Backend normalization error"), _("Backend normalization error"))

        self._time_field = time_field

    @staticmethod
    def _value_escape(value):
        if not isinstance(value, compat.STRING_TYPES):
            value = str(value)

        return value.replace("\\", "\\\\").replace("'", "\\'")

    def parse_paths(self, paths, type):
        """
        Parse paths and turn them into a structure that can be used by the backend.

        @param paths: List of paths in natural syntax (eg. ["foo.bar", "count(foo.id)"])
        @type paths: list
        @param type: type of backend
        @type type: string
        @return: The paths as a structure that can easily be used by the backend.
        """
        return [p.format(backend=type, time_field=self._time_field) for p in paths], []

    def parse_criteria(self, criteria, type):
        """
        Parse criteria and turn them into a structure that can be used by the backend.

        @param criteria: Criteria string (eg. "foo.bar == 42 || foo.id = 23")
        @type criteria: str
        @param type: type of backend
        @type type: string
        @return: The criteria as a structure that can easily be used by the backend.
        """
        return criteria


    def parse_criterion(self, path, operator, value, type):
        path = path.format(backend=type, time_field=self._time_field)

        if operator in ("=", "==") and value is None:
            return "!%s" % (path)

        if operator in ("!=", None) and value is None:
            return path

        return "%s %s '%s'" % (path, operator, self._value_escape(value))



class Criterion(json.JSONObject):
    def _init(self, left, operator, right):
        self.left, self.operator, self.right = left, operator, right

    def __init__(self, left=None, operator=None, right=None):
        json.JSONObject.__init__(self)
        self._init(left, operator, right)

    def get_paths(self):
        if self.operator in ("&&", "||"):
            return self.left.get_paths() | self.right.get_paths()

        res = set()
        if self.left:
            res.add(self.left)

        return res

    def _resolve(self, type):
        list(hookmanager.trigger("HOOK_CRITERION_LOAD", self))

        if not type:
            return " ".join(str(i) for i in [self.left, self.operator, self.right])

        return env.dataprovider._type_handlers[type].parse_criterion(self.left, self.operator, self.right, type)

    def to_string(self, type=None):
        if not self.left:
            return ""

        if self.operator in ("&&", "||"):
            out = "(" + " ".join((self.left.to_string(type), self.operator, self.right.to_string(type))) + ")"
        else:
            out = self._resolve(type)

        return out

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

    def __nonzero__(self):
        return self.left is not None

    def __copy__(self):
        return Criterion(self.left, self.operator, self.right)

    def __json__(self):
        return [self.left, self.operator, self.right]

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



class DataProviderManager(pluginmanager.PluginManager):
    def __init__(self):
        self._type_handlers = {}
        self._backends = {}

        pluginmanager.PluginManager.__init__(self, "prewikka.dataprovider.type")
        for k in self.keys():
            try:
                p = self[k]()
            except error.PrewikkaUserError as err:
                env.log.warning("%s: plugin failed to load: %s" % (self[k].__name__, err))
                continue

            normalizer = getattr(p, "normalizer", None)
            if not isinstance(normalizer, (types.NoneType, DataProviderNormalizer)):
                raise DataProviderError(_("Invalid normalizer for '%s' datatype") % k)

            self._type_handlers[k] = normalizer

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
                raise error.PrewikkaUserError(_("Configuration error"),
                                              N_("Only one manager should be configured for '%s' backend", p.type))

            self._backends[p.type] = p

    @staticmethod
    def _parse_path(path):
        tmp = path.partition('.')
        if not tmp[1]:
            return

        tmp = tmp[0].rpartition('(')[2]
        # Exclude generic paths, eg. "{backend}.{time_field}".
        if tmp != '{backend}':
            return tmp

    def _guess_data_type(self, paths, criteria=None):
        res = set()

        for path in set(paths) | criteria.get_paths():
            path = self._parse_path(path)
            if path:
                res.add(path)

        if len(res) != 1:
            raise DataProviderError("Unable to guess data type: incompatible paths")

        return list(res)[0]

    def _check_data_type(self, type, *args):
        if not type:
            type = self._guess_data_type(*args)

        if type not in self._type_handlers or type not in self._backends:
            raise NoBackendError("No backend available for '%s' datatype" % type)

        return type

    def _normalize(self, type, paths=None, criteria=None):
        if paths is None:
            paths = []

        if criteria is None:
            criteria = Criterion()

        type = self._check_data_type(type, paths, criteria)

        compcrit = None
        paths_types = []
        normalizer = self._type_handlers[type]

        list(hookmanager.trigger("HOOK_DATAPROVIDER_CRITERIA_PREPARE", criteria, type))

        if normalizer:
            paths, paths_types = normalizer.parse_paths(paths, type)
            if criteria:
                compcrit = normalizer.parse_criteria(criteria.to_string(type), type)

        return type, paths, paths_types, compcrit

    def query(self, paths, criteria=None, distinct=0, limit=-1, offset=-1, type=None):
        type, paths, paths_types, criteria = self._normalize(type, paths, criteria)

        start = time.time()
        results = self._backends[type].get_values(paths, criteria, distinct, limit, offset)
        results.duration = time.time() - start

        results._paths = paths
        results._paths_types = paths_types

        return results

    def get_by_id(self, type, id_):
        return self._backends[type].get_by_id(id_)

    def get(self, criteria=None, order_by="time_desc", limit=-1, offset=-1, type=None):
        if order_by not in ("time_asc", "time_desc"):
            raise DataProviderError("Invalid value for parameter 'order_by'")

        type, _, _, criteria = self._normalize(type, criteria=criteria)
        return self._backends[type].get(criteria, order_by, limit, offset)

    def delete(self, criteria=None, paths=None, type=None):
        type, paths, _, criteria = self._normalize(type, paths, criteria)
        return self._backends[type].delete(criteria, paths)

    def insert(self, data, criteria=None, type=None):
        paths, values = zip(*data.items())
        type, paths, _, criteria = self._normalize(type, paths, criteria)
        return self._backends[type].insert(zip(paths, values), criteria)

    def update(self, data, criteria=None, type=None):
        paths, values = zip(*data.items())
        type, paths, _, criteria = self._normalize(type, paths, criteria)
        return self._backends[type].update(zip(paths, values), criteria)

    def has_type(self, wanted_type):
        return wanted_type in self._backends
