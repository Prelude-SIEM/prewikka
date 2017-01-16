# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
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

_sentinel = object()


def _register_decorator(hook):
    def decorator(func):
        lst = getattr(func, "__prewikka_hook__", [])
        if not lst:
            setattr(func, "__prewikka_hook__", lst)

        lst.append(hook)
        return func

    return decorator


class HookRegistrar(object):
    def __init__(self, *args, **kwargs):
        for name, ref in self.__class__.__dict__.items():
            for hook in getattr(ref, "__prewikka_hook__", []):
                hookmgr.register(hook, getattr(self, name))


class HookManager:
    def __init__(self):
        self._hooks = { }

    def __contains__(self, hook):
        return hook in self._hooks

    def unregister(self, hook=None, method=None):
        if hook and method:
            self._hooks[hook].remove(method)
        else:
            for i in self._hooks:
                self._hooks[i] = []

    def register(self, hook, method=_sentinel):
        if method is not _sentinel:
            self._hooks.setdefault(hook, []).append(method)
        else:
            return _register_decorator(hook)

    def trigger(self, hook, *args, **kwargs):
        wtype = kwargs.pop("type", None)

        for cb in self._hooks.setdefault(hook, []):
            if callable(cb):
                result = cb(*args, **kwargs)
            else:
                result = cb

            if result and wtype and not isinstance(result, wtype):
                raise Exception("Hook '%s' expect return type of '%s' but got '%s'" % (hook, wtype, type(result)))

            yield result


hookmgr = HookManager()

trigger = hookmgr.trigger
register = hookmgr.register
unregister = hookmgr.unregister
