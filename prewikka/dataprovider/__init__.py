# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
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
import itertools
import time

from datetime import datetime, timedelta
from enum import Enum

from prewikka import compat, error, hookmanager, pluginmanager
from prewikka.utils import AttrObj, CachingIterator, json
from prewikka.utils.timeutil import parser, tzutc


OPERATORS = {
    "=": N_("Equal"),
    "=*": N_("Equal (case-insensitive)"),
    "!=": N_("Not equal"),
    "!=*": N_("Not equal (case-insensitive)"),
    "~": N_("Regular expression"),
    "~*": N_("Regular expression (case-insensitive)"),
    "!~": N_("Not regular expression"),
    "!~*": N_("Not regular expression (case-insensitive)"),
    "<": N_("Lesser than"),
    "<=": N_("Lesser or equal"),
    ">": N_("Greater than"),
    ">=": N_("Greater or equal"),
    "<>": N_("Substring"),
    "<>*": N_("Substring (case-insensitive)"),
    "!<>": N_("Not substring"),
    "!<>*": N_("Not substring (case-insensitive)")
}

COMPOSITE_TIME_FIELD = "_time_field"


def PathInfo(path, value_type, operators=[], value_accept=[], type=None):
    assert(operators or type)

    if not operators:
        base = env.dataprovider._type_handlers[type]
        operators = base.get_operator_by_datatype(value_type, default=base.get_operator_by_datatype(None, default=[]))

    return AttrObj(path=path, field=".".join(path.split(".")[1:]), type=value_type, operators=operators, value_accept=value_accept)


def PathValue(value, label=None, color=None):
    return AttrObj(value=value, label=label or value, color=color)


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


class NoBackendError(error.PrewikkaUserError):
    def __init__(self, type_):
        error.PrewikkaUserError.__init__(
            self, N_("Backend error"), N_("No backend available for '%s' datatype", type_)
        )


class InvalidPathError(error.PrewikkaUserError):
    def __init__(self, path, details=None):
        error.PrewikkaUserError.__init__(
            self, N_("Syntax error"), N_("Unknown path: %s", path), details=details
        )


class ParserError(error.PrewikkaUserError):
    def __init__(self, details=None):
        error.PrewikkaUserError.__init__(
            self, N_("Syntax error"), N_("Could not parse input"), details=details
        )


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

            elif type is timedelta:
                return timedelta(seconds=int(value))

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
            return self.__class__(obj, curpath)

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


class DataProviderInstance(pluginmanager.PluginBase):
    type = None
    TYPE_OPERATOR_MAPPING = {}

    def get_values(self, paths, criteria, distinct, limit, offset):
        """
        Retrieves data corresponding to the given paths. If criteria are given,
        only values matching these criteria will be retrieved.

        @param paths: Selected paths
        @type paths: list
        @param criteria: Search criteria
        @type criteria: list
        @param distinct: Control whether duplicate entries should be removed (True) or kept (False)
        @type distinct: bool
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

    def get_properties(self):
        pass

    def _get_path_values(self, path):
        pass


class DataProviderBackend(pluginmanager.PluginBase):
    _instances = {}
    _default_instance = None

    def __init__(self):
        pluginmanager.PluginBase.__init__(self)
        self._default_instance = DataProviderInstance()

    def post_load(self):
        pass

    def __getattr__(self, attr):
        return getattr(self._default_instance, attr)


class DataProviderBase(pluginmanager.PluginBase):
    dataprovider_type = None
    dataprovider_label = None
    dataprovider_continuous = False
    TYPE_OPERATOR_MAPPING = {}

    def __init__(self, time_field):
        pluginmanager.PluginBase.__init__(self)

        if isinstance(time_field, tuple):
            self._time_field = COMPOSITE_TIME_FIELD
            self._start_time_field, self._end_time_field = time_field
        else:
            self._time_field = time_field
            self._start_time_field, self._end_time_field = time_field, time_field

    def post_load(self):
        pass

    def get_common_paths(self, index=False):
        return []

    def format_path(self, path):
        return path.format(
            backend=self.dataprovider_type,
            time_field=self._time_field,
            start_time_field=self._start_time_field,
            end_time_field=self._end_time_field
        )

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

    def get_paths(self):
        raise error.NotImplementedError

    def get_path_type(self, path):
        raise error.NotImplementedError

    def register_path(self, path, type):
        raise error.NotImplementedError

    def get_path_info(self, path):
        return PathInfo(path, env.dataprovider.get_path_type(path), value_accept=self._get_path_values(path), type=self.dataprovider_type)

    # The following methods might be implemented by the backend or by the type itself.
    def _get_path_values(self, path):
        backend = env.dataprovider._backends.get(self.dataprovider_type)
        if backend:
            return backend._get_path_values(path)

    def get_properties(self):
        backend = env.dataprovider._backends.get(self.dataprovider_type)
        if backend:
            return backend.get_properties()

    def get_operator_by_datatype(self, datatype, default=None):
        mapping = None
        if self.dataprovider_type in env.dataprovider._backends:
            mapping = env.dataprovider._backends[self.dataprovider_type].TYPE_OPERATOR_MAPPING

        if not mapping:
            mapping = self.TYPE_OPERATOR_MAPPING

        return mapping.get(datatype, default)

    def get_indexation_path(self, path):
        raise error.NotImplementedError


class _CriterionOperatorFamily(Enum):
    BOOLEAN = 0
    STANDARD = 1
    REGEX = 2
    SUBSTRING = 3


# ["String1", StringN, "ENUM_VALUE"], Family, Negated, Case-Insensitive
_CriterionOperatorList = [
    (["&&", "AND"], _CriterionOperatorFamily.BOOLEAN, False, False),
    (["||", "OR"], _CriterionOperatorFamily.BOOLEAN, False, False),
    (["!", "NOT"], _CriterionOperatorFamily.BOOLEAN, True, False),

    # STANDARD
    (["=", "==", "EQUAL"], _CriterionOperatorFamily.STANDARD, False, False),
    (["=*", "EQUAL_NOCASE"], _CriterionOperatorFamily.STANDARD, False, True),
    (["!=", "NOT_EQUAL"], _CriterionOperatorFamily.STANDARD, True, False),
    (["!=*", "NOT_EQUAL_NOCASE"], _CriterionOperatorFamily.STANDARD, True, True),
    (["<", "LOWER"], _CriterionOperatorFamily.STANDARD, False, False),
    ([">", "GREATER"], _CriterionOperatorFamily.STANDARD, False, False),
    (["<=", "LOWER_OR_EQUAL"], _CriterionOperatorFamily.STANDARD, False, False),
    ([">=", "GREATER_OR_EQUAL"], _CriterionOperatorFamily.STANDARD, False, False),

    # REGEX
    (["~", "REGEX"], _CriterionOperatorFamily.REGEX, False, False),
    (["!~", "NOT_REGEX"], _CriterionOperatorFamily.REGEX, True, False),
    (["~*", "REGEX_NOCASE"], _CriterionOperatorFamily.REGEX, False, True),
    (["!~*", "NOT_REGEX_NOCASE"], _CriterionOperatorFamily.REGEX, True, True),

    # SUBSTRING
    (["<>", "SUBSTR"], _CriterionOperatorFamily.SUBSTRING, False, False),
    (["!<>", "NOT_SUBSTR"], _CriterionOperatorFamily.SUBSTRING, True, False),
    (["<>*", "SUBSTR_NOCASE"], _CriterionOperatorFamily.SUBSTRING, False, True),
    (["!<>*", "NOT_SUBSTR_NOCASE"], _CriterionOperatorFamily.SUBSTRING, True, True),
]


class _CriterionEnum(Enum):
    @property
    def family(self):
        return _CriterionOperatorList[self.value][1]

    @property
    def negated(self):
        return _CriterionOperatorList[self.value][2]

    @property
    def case_insensitive(self):
        return _CriterionOperatorList[self.value][3]

    @property
    def is_regex(self):
        return self.family is _CriterionOperatorFamily.REGEX

    @property
    def is_boolean(self):
        return self.family is _CriterionOperatorFamily.BOOLEAN

    @property
    def is_substring(self):
        return self.family is _CriterionOperatorFamily.SUBSTRING

    def __json__(self):
        return self.name


CriterionOperator = _CriterionEnum(
    value="CriterionOperator",
    names=itertools.chain.from_iterable(
        itertools.product(v[0], [k]) for k, v in enumerate(_CriterionOperatorList)
    )
)


class Criterion(json.JSONObject):
    def __init__(self, left=None, operator=None, right=None):
        json.JSONObject.__init__(self)

        if isinstance(operator, text_type):
            operator = CriterionOperator[operator]

        self._init(left, operator, right)

    def _init(self, left, operator, right):
        self.left, self.operator, self.right = left, operator, right

    def get_paths(self):
        res = set()
        if not self:
            return res

        if not self.operator.is_boolean:
            res.add(self.left)
        else:
            if self.left:
                res |= self.left.get_paths()

            res |= self.right.get_paths()

        return res

    def _compile(self, base, format_only=False):
        if not self:
            return copy.copy(self)

        if self.operator.is_boolean:
            left = self.left._compile(base, format_only) if self.left else None
            return Criterion(left, self.operator, self.right._compile(base, format_only))

        left = base.format_path(self.left)
        if format_only:
            return Criterion(left, self.operator, self.right)

        tpl = [left, self.right]

        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_WRITE", tpl))
        return base.compile_criterion(Criterion(tpl[0], self.operator, tpl[1]))

    @staticmethod
    def _value_escape(value):
        if isinstance(value, (int, float)):
            return value

        if isinstance(value, timedelta):
            return int(value.total_seconds())

        if not isinstance(value, compat.STRING_TYPES):
            value = text_type(value)

        return "'%s'" % value.replace("'", "\\'")

    def _criterion_to_string(self, path, operator, value):
        if value is None:
            if operator == CriterionOperator.EQUAL:
                return "!%s" % (path)

            if operator == CriterionOperator.NOT_EQUAL:
                return path

        return "%s %s %s" % (path, operator.name, self._value_escape(value))

    def to_string(self, noroot=False, _depth=0):
        if not self:
            return ""

        if self.operator.is_boolean:
            if self.operator == CriterionOperator.NOT:
                res = "!%s" % self.right.to_string(noroot, _depth + 1)
            else:
                res = " ".join((self.left.to_string(noroot, _depth + 1), self.operator.name, self.right.to_string(noroot, _depth + 1)))

            return res if _depth == 0 else "(%s)" % res

        lst = [self.left, self.operator, self.right]
        if noroot:
            lst[0] = lst[0].split(".", 1)[-1]

        return self._criterion_to_string(*lst)

    def to_list(self, type=None):
        if not self:
            return []

        if self.operator.is_boolean:
            return (self.left.to_list(type) if self.left else []) + self.right.to_list(type)

        return [self]

    def flatten(self):
        if not self or not self.operator.is_boolean:
            return self

        ret = AttrObj(operator=self.operator, operands=[])

        for operand in (self.left.flatten(), self.right.flatten()):
            if operand.operator == self.operator:
                ret.operands += operand.operands
            else:
                ret.operands.append(operand)

        return ret

    def compile(self, type):
        base = env.dataprovider._type_handlers[type]
        return base.compile_criteria(self._compile(base))

    def format(self, type):
        return self._compile(env.dataprovider._type_handlers[type], format_only=True)

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
        return self.operator is not None

    def __copy__(self):
        return Criterion(self.left, self.operator, self.right)

    def __json__(self):
        return {"left": self.left, "operator": self.operator, "right": self.right}

    def __iadd__(self, other):
        return self._apply_self(CriterionOperator.AND, other)

    def __ior__(self, other):
        return self._apply_self(CriterionOperator.OR, other)

    def __iand__(self, other):
        return self._apply_self(CriterionOperator.AND, other)

    def __add__(self, other):
        return self._apply_new(CriterionOperator.AND, other)

    def __or__(self, other):
        return self._apply_new(CriterionOperator.OR, other)

    __and__ = __add__
    __nonzero__ = __bool__


class DataProviderManager(pluginmanager.PluginManager):
    def __init__(self, autoupdate=False):
        pluginmanager.PluginManager.__init__(self, "prewikka.dataprovider.type", autoupdate=autoupdate)

        self._type_handlers = {}
        self._backends = {}

    def load(self, autoupdate=False):
        for k in self.keys():
            try:
                p = self.initialize_plugin(self[k])
            except Exception:
                continue

            p.dataprovider_type = k
            self._type_handlers[k] = p

        for plugin in pluginmanager.PluginManager("prewikka.dataprovider.backend", autoupdate=autoupdate):

            if plugin.type not in self._type_handlers:
                plugin.error = N_("No handler configured for '%s' datatype", plugin.type)
                env.log.warning("%s: plugin loading failed: %s" % (plugin.__name__, plugin.error))
                continue

            try:
                p = self.initialize_plugin(plugin)
            except Exception:
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

    def check_datatype(self, type, *args, **kwargs):
        if not type:
            type = self.guess_datatype(*args)

        if type not in self._type_handlers or (kwargs.get("require_backend", True) and type not in self._backends):
            raise NoBackendError(type)

        return type

    def _normalize(self, type, paths=None, criteria=None):
        if paths is None:
            paths = []

        if criteria is None:
            criteria = Criterion()
        else:
            criteria = copy.copy(criteria)

        type = self.check_datatype(type, paths, criteria)

        parsed_paths = paths
        paths_types = []

        plugin = self._type_handlers[type]

        paths = plugin.format_paths(paths)
        parsed_paths, paths_types = plugin.parse_paths(paths)

        for c in filter(None, hookmanager.trigger("HOOK_DATAPROVIDER_CRITERIA_PREPARE", type)):
            criteria += c

        return AttrObj(type=type, paths=paths, parsed_paths=parsed_paths, paths_types=paths_types, criteria=criteria.compile(type))

    def query(self, paths, criteria=None, distinct=False, limit=-1, offset=0, type=None, **kwargs):
        o = self._normalize(type, paths, criteria)

        start = time.time()
        results = self._backends[o.type].get_values(o.parsed_paths, o.criteria, distinct, limit, offset, **kwargs)
        results.duration = time.time() - start

        results._paths = o.paths
        results._paths_types = o.paths_types

        return results

    def get_by_id(self, type, id_):
        return self._backends[type].get_by_id(id_)

    def get(self, criteria=None, order_by=["{backend}.{time_field}/order_desc"], limit=-1, offset=0, type=None):
        o = self._normalize(type, order_by, criteria)
        return self._backends[o.type].get(o.criteria, o.paths, limit, offset)

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

    def get_types(self, public=False, require_backend=True):
        for k, v in self._type_handlers.items():
            if require_backend and k not in self._backends:
                continue

            if (not public) or v.dataprovider_label:
                yield k

    def has_type(self, wanted_type):
        return wanted_type in self._backends

    def get_properties(self, type):
        return self._type_handlers[type].get_properties()

    def get_label(self, type):
        return self._type_handlers[type].dataprovider_label

    def format_path(self, path, type=None):
        if not type:
            type = self.guess_datatype([path])

        return self._type_handlers[type].format_path(path)

    def register_path(self, path, path_type, type=None):
        if not type:
            type = self.guess_datatype([path])

        return self._type_handlers[type].register_path(path, path_type)

    def get_paths(self, type):
        return self._type_handlers[type].get_paths()

    def get_common_paths(self, type, index=False):
        return self._type_handlers[type].get_common_paths(index)

    def get_path_info(self, path, type=None):
        type = self.check_datatype(type, [path], require_backend=False)
        return self._type_handlers[type].get_path_info(path)

    def get_path_type(self, path, type=None):
        type = self.check_datatype(type, [path], require_backend=False)
        return self._type_handlers[type].get_path_type(path)

    def get_operator_by_datatype(self, type, datatype, default=None):
        return self._type_handlers[type].get_operator_by_datatype(datatype, default=None)

    def get_indexation_path(self, path):
        type = self.guess_datatype([path])
        return self._type_handlers[type].get_indexation_path(path)

    def is_continuous(self, type):
        # Whether data can be interpolated (e.g. for metric-type dataproviders)
        return self._type_handlers[type].dataprovider_continuous
