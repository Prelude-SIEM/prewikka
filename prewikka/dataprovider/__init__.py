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

import types, time
from datetime import datetime

from prewikka import pluginmanager, error, env, hookmanager
from prewikka.utils.timeutil import parser
from prewikka.utils import CachingIterator


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

    def parse_paths(self, paths, type):
        """
        Parse paths and turn them into a structure that can be used by the backend.

        @param paths: List of paths in natural syntax (eg. ["foo.bar", "count(foo.id)"])
        @type paths: list
        @param type: type of backend
        @type type: string
        @return: The paths as a structure that can easily be used by the backend.
        """

        parsed_paths = []
        paths_types = []

        for path in paths:
            try:
                parsed_paths.append(path % { 'backend' : type, 'time_field' : self._time_field })
            except:
                parsed_paths.append(path)

        return parsed_paths, paths_types

    def parse_criteria(self, criteria, type):
        """
        Parse criteria and turn them into a structure that can be used by the backend.

        @param criteria: List of criteria in natural syntax (eg. ["foo.bar == 42 || foo.id = 23"])
        @type criteria: list
        @param type: type of backend
        @type type: string
        @return: The criteria as a structure that can easily be used by the backend.
        """

        parsed_criteria = []

        for criterion in criteria:
            try:
                parsed_criteria.append(criterion % { 'backend' : type, 'time_field' : self._time_field })
            except:
                parsed_criteria.append(criterion)

        return parsed_criteria


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

    def _guess_data_type(self, paths, criteria=None):
        res = set()
        for path in paths:
            tmp = path.partition('.')
            if not tmp[1]:
                continue
            tmp = tmp[0].rpartition('(')[2]
            # Exclude generic paths, eg. "%(backend)s.%(time_field)s".
            if tmp != 'backend)s':
                res.add(tmp)

        # FIXME Try to guess the backend using criteria first
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
            criteria = []

        paths_types = []
        normalizer = self._type_handlers[type]

        if normalizer:
            paths, paths_types = normalizer.parse_paths(paths, type)
            criteria = normalizer.parse_criteria(criteria, type)

        return paths, paths_types, criteria

    def query(self, paths, criteria=None, distinct=0, limit=-1, offset=-1, type=None):
        type = self._check_data_type(type, paths, criteria)
        paths, paths_types, criteria = self._normalize(type, paths, criteria)

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

        type = self._check_data_type(type, [], criteria)
        criteria = self._normalize(type, criteria=criteria)[2]
        return self._backends[type].get(criteria, order_by, limit, offset)

    def delete(self, criteria=None, type=None):
        type = self._check_data_type(type, [], criteria)
        criteria = self._normalize(type, criteria=criteria)[2]
        return self._backends[type].delete(criteria)

    def insert(self, data, criteria=None, type=None):
        type = self._check_data_type(type, data.keys())
        criteria = self._normalize(type, criteria=criteria)[2]
        return self._backends[type].insert(data, criteria)

    def update(self, data, criteria=None, type=None):
        type = self._check_data_type(type, data.keys(), criteria)
        criteria = self._normalize(type, criteria=criteria)[2]
        return self._backends[type].update(data, criteria)

    def has_type(self, wanted_type):
        return wanted_type in self._backends
