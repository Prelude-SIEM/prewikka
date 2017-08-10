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

from prewikka import registrar

_sentinel = object()


class HookManager(object):
    def __init__(self):
        self._hooks = {}

    def __contains__(self, hook):
        return hook in self._hooks

    def unregister(self, hook=None, method=None, exclude=[]):
        if hook and method:
            self._hooks[hook].remove(method)
        elif hook:
            self._hooks[hook] = []
        else:
            for i in set(self._hooks) - set(exclude):
                self._hooks[i] = []

    def register(self, hook, _regfunc=_sentinel):
        if _regfunc is not _sentinel:
            self._hooks.setdefault(hook, []).append(_regfunc)
        else:
            return registrar.DelayedRegistrar.make_decorator("hook", self.register, hook)

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
