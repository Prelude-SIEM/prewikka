# Copyright (C) 2017 CS-SI. All Rights Reserved.
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

import functools

_ATTRIBUTE = "__delayreg__"


class DelayedRegistrar(object):
    @staticmethod
    def make_decorator(type, regfunc, *args, **kwargs):
        def indecorator(func):
            d = getattr(func, _ATTRIBUTE, {})
            if not d:
                setattr(func, _ATTRIBUTE, d)

            d.setdefault(type, []).append(functools.partial(regfunc, *args, **kwargs))
            return func

        return indecorator

    def __init__(self, *args, **kwargs):
        for name in dir(self):
            if isinstance(getattr(type(self), name, None), property):
                continue

            ref = getattr(self, name)
            for flist in getattr(ref, _ATTRIBUTE, {}).values():
                for i in flist:
                    i(ref)
