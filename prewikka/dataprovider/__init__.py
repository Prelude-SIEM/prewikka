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

import types
from datetime import datetime

from prewikka import pluginmanager, error, env
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
        raise error.PrewikkaUserError(N_("Conversion error"),
                                      N_("Value %(value)r cannot be converted to %(type)s" % {"value": date, "type": "datetime"}))
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
    def __init__(self, items, types):
        CachingIterator.__init__(self, items)
        self._types = types

    def preprocess_value(self, value):
        if value is None:
            return None

        type = self._types[len(self._cache)]
        try:
            return TYPES_FUNC_MAP[type](value)
        except (KeyError, ValueError):
            raise error.PrewikkaUserError(N_("Conversion error"),
                                          N_("Value %(value)r cannot be converted to %(type)s" % {"value": value, "type": type}))


class QueryResults(CachingIterator):
    def __init__(self, duration=-1, count=None, rows=None):
        CachingIterator.__init__(self, rows)
        self._count = count
        self._duration = duration
        self.paths_types = []

    @property
    def duration(self):
        return self._duration

    def preprocess_value(self, value):
        return QueryResultsRow(value, self.paths_types)


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
    def parse_paths(self, paths, type):
        """
        Parse paths and turn them into a structure
        that can be used by the backend.

        @param paths: List of paths in natural syntax
            (eg. ["foo.bar", "count(foo.id)"])
        @type paths: list
        @param type: type of backend
        @type type: string
        @return: The paths as a structure that can easily
            be used by the backend.
        """
        pass

    def parse_criteria(self, criteria, type):
        """
        Parse criteria and turn them into a structure
        that can be used by the backend.

        @param criteria: List of criteria in natural syntax
            (eg. ["foo.bar == 42 || foo.id = 23"])
        @type criteria: list
        @param type: type of backend
        @type type: string
        @return: The criteria as a structure that can easily
            be used by the backend.
        """
        pass


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
                env.log.warning("%s: plugin failed to load: %s" % (
                    plugin.__name__,
                    _("No handler configured for '%s' datatype" % plugin.type)))
                continue

            try:
                p = plugin()
            except error.PrewikkaUserError as err:
                env.log.warning("%s: plugin failed to load: %s" % (plugin.__name__, err))
                continue

            if p.type in self._backends:
                raise error.PrewikkaUserError(_("Configuration error"),
                                              _("Only one manager should be configured for '%s' backend") % p.type)

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

    def query(self, paths, criteria=None, distinct=0, limit=-1, offset=-1, type=None):
        if not type:
            type = self._guess_data_type(paths, criteria)

        if type not in self._type_handlers or type not in self._backends:
            raise NoBackendError("No backend available for '%s' datatype" % type)

        if criteria is None:
            criteria = []

        normalizer = self._type_handlers[type]
        paths_types = []
        if normalizer:
            paths, paths_types = normalizer.parse_paths(paths, type)
            criteria = normalizer.parse_criteria(criteria, type)

        results = self._backends[type].get_values(paths, criteria, distinct, limit, offset)
        results.paths_types = paths_types
        return results

    def has_type(self, wanted_type):
        return wanted_type in self._backends
