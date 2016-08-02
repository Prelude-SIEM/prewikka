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

from prewikka import pluginmanager, error, env


class DataProviderError(Exception):
    pass


class NoBackendError(DataProviderError):
    pass


class QueryResults:
    def __init__(self, duration=-1, count=None, rows=None):
        self._duration = duration
        self._rows = iter(rows)
        self._count = count
        self._cache = []

    @property
    def duration(self):
        return self._duration

    def __len__(self):
        if self._count is None:
            for _dummy in iter(self):
                pass # Throw the value away: we don't need it
            self._count = len(self._cache)
        return self._count

    def __iter__(self):
        for row in self._cache:
            yield row

        while True:
            res = next(self._rows)
            self._cache.append(res)
            yield res

    def __getitem__(self, key):
        # Normalize the input
        if isinstance(key, slice):
            start = key.start
            if not start:
                start = 0
            elif start < 0:
                start = min(0, len(self) + start)
            stop = key.stop
            if not stop:
                stop = len(self)
            elif stop < 0:
                stop = min(0, len(self) + stop)
        else:
            start = key
            if start < 0:
                start = min(0, len(self) + start)
            stop = start + 1

        # Fetch as many rows as necessary from the backend into the cache
        try:
            for i in xrange(stop - len(self._cache)):
                self._cache.append(next(self._rows))
        except StopIteration:
            pass

        # Return the appropriate slice or value
        if isinstance(key, slice):
            return self._cache[start : stop : key.step]
        return self._cache[start]


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
        if normalizer:
            paths = normalizer.parse_paths(paths, type)
            criteria = normalizer.parse_criteria(criteria, type)

        results = self._backends[type].get_values(paths, criteria, distinct, limit, offset)

        return results

    def has_type(self, wanted_type):
        return wanted_type in self._backends

