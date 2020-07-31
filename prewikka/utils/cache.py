# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
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

import collections
import functools

_CacheInfo = collections.namedtuple("CacheInfo", ["hits", "misses", "size"])


class _Cache(object):
    _missing = object()

    def __init__(self, func):
        self._cache = {}
        self._cached_func = func
        self._hits = self._misses = 0

    def _set(self, key, value):
        self._cache[key] = value
        return value

    def _get(self, *args, **kwargs):
        key = (args, tuple(kwargs.items()))
        try:
            value = self._cache.get(key, self._missing)
            if value is not self._missing:
                self._hits = self._hits + 1
                return value

            self._misses = self._misses + 1
            return self._set(key, self._cached_func(*args, **kwargs))

        except TypeError as e:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            env.log.critical("request not cachable: %s(%s): %s" % (self._cached_func.__name__, repr(key), e))
            return self._cached_func(*args, **kwargs)

    def clear(self):
        self._cache.clear()

    def infos(self):
        return _CacheInfo(self._hits, self._misses, len(self._cache))


class _memoize(object):
    def __init__(self, func, name):
        self.func = func
        self.cache_objname = name

    def __call__(self, obj, *args, **kwargs):
        return self._setup_cache(obj)._get(obj, *args, **kwargs)

    def _setup_cache(self, obj):
        cache = getattr(obj, self.cache_objname, None)
        if not cache:
            cache = _Cache(self.func)
            setattr(obj, self.cache_objname, cache)

        return cache

    def __get__(self, obj, objtype):
        return functools.partial(self.__call__, obj)


class _memoize_property(_memoize):
    def __init__(self, func, name):
        self._set_func = None
        _memoize.__init__(self, func, name)

    def setter(self, func):
        self._set_func = func
        return self

    def __set__(self, obj, value):
        if not self._set_func:
            return

        self._set_func(obj, value)
        self._setup_cache(obj)._set((obj,), value)

    def __get__(self, obj, objtype):
        return _memoize.__get__(self, obj, objtype)()


class _request_memoize(_memoize):
    def _setup_cache(self, obj):
        return _memoize._setup_cache(self, env.request.cache)


class _request_memoize_property(_request_memoize, _memoize_property):
    pass


class memoize(object):
    """
        Decorator that will cache the decorated function result value. The cache is stored into
        the instance of the object providing the method.

        Note that calling the cached function with different arguments result in different cache
        entry.

        Usage :

        @memoize("expensive_cache")
        def get_expensive_stuff(self, arg1, argN):
            ... time consuming stuff ...

        The created cache object provide the following API:
        - Cache hits/misses/size statistics:
          self.expensive_cache.infos()

        - Clearing the cache:
          self.expensive_cache.clear()
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        return _memoize(func, self.name)


class memoize_property(object):
    """
        Property decorator that cache the method result value. The method is accessible as a Python
        @property, and the cache is stored into the instance of the object providing the method.

        Usage :

        @memoize_property("my_property_cache")
        def my_property(self):
            ... time consuming stuff ...

        The created cache object provide the following API:
        - Cache hits/misses/size statistics:
          self.my_property_cache.infos()

        - Clearing the cache:
          self.my_property_cache.clear()
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        return _memoize_property(func, self.name)


class request_memoize(object):
    """
        Decorator that will cache the decorated function result value only in the context of the
        current request. The cache will be stored into the env.request.cache object.

        Note that calling the cached function with different arguments result in different cache
        entry.

        Usage :

        @request_memoize("expensive_cache")
        def get_expensive_stuff(self, arg1, arg2):
            ... time consuming things ...

        The created caching object provide the following API:
        - Cache hits/misses/size statistics:
          env.request.cache.expensive_cache.infos()

        - Clearing the cache:
          env.request.cache.expensive_cache.clear()
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        return _request_memoize(func, self.name)


class request_memoize_property(object):
    """
        Property decorator that cache the method result value only in the context of the current
        request. The method is accessible like a Python @property, and the cache is stored into
        the env.request.cache object.

        Usage :

        @request_memoize_property("my_property_cache")
        def my_property(self):
            pass

        The created caching object provide the following API:
        - Cache hits/misses/size statistics:
          env.request.cache.my_property_cache.infos()

        - Clearing the cache:
          env.request.cache.my_property_cache.clear()
    """
    def __init__(self, name):
        self.name = name

    def __call__(self, func):
        return _request_memoize_property(func, self.name)
