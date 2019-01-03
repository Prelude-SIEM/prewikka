# Copyright (C) 2016-2019 CS-SI. All Rights Reserved.
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

import operator
from prewikka import registrar

_sentinel = object()


class HookManager(object):
    def __init__(self):
        self._hooks = {}

    def __contains__(self, hook):
        return hook in self._hooks

    def unregister(self, hook=None, method=None, exclude=[]):
        if hook and method:
            self._hooks[hook] = [(order, func) for order, func in self._hooks[hook] if func != method]
        elif hook:
            self._hooks[hook] = []
        else:
            for i in set(self._hooks) - set(exclude):
                self._hooks[i] = []

    def register(self, hook, _regfunc=_sentinel, _order=2**16):
        if _regfunc is not _sentinel:
            self._hooks.setdefault(hook, []).append((_order, _regfunc))
        else:
            return registrar.DelayedRegistrar.make_decorator("hook", self.register, hook, _order=_order)

    def trigger(self, hook, *args, **kwargs):
        wtype = kwargs.pop("type", None)
        _except = kwargs.pop("_except", None)

        for order, cb in sorted(self._hooks.setdefault(hook, []), key=operator.itemgetter(0)):
            if not callable(cb):
                result = cb
            else:
                try:
                    result = cb(*args, **kwargs)
                except Exception as e:
                    if _except:
                        _except(e)
                        continue
                    else:
                        raise

            if result and wtype and not isinstance(result, wtype):
                raise TypeError("Hook '%s' expect return type of '%s' but got '%s'" % (hook, wtype, type(result)))

            yield result


hookmgr = HookManager()
trigger = hookmgr.trigger
register = hookmgr.register
unregister = hookmgr.unregister
