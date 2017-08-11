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

import datetime
import json

from prewikka.utils import html

_TYPES = {}


class _JSONMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        nclass = super(_JSONMetaClass, cls).__new__(cls, clsname, bases, attrs)

        _TYPES[nclass.__name__] = nclass

        return nclass


class JSONObject(object):
    __metaclass__ = _JSONMetaClass

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def __jsonobj__(self):
        return {"__prewikka_class__": (self.__class__.__name__, self.__json__())}


class PrewikkaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__jsonobj__"):
            return obj.__jsonobj__()

        elif hasattr(obj, "__json__"):
            return obj.__json__()

        elif isinstance(obj, datetime.datetime):
            return text_type(obj)

        return json.JSONEncoder.default(self, obj)


def _object_hook(obj):
    cls = obj.get("__prewikka_class__")
    if cls:
        return _TYPES[cls[0]].from_json(cls[1])

    return obj


def load(*args, **kwargs):
    return json.load(*args, object_hook=_object_hook, **kwargs)


def loads(*args, **kwargs):
    return json.loads(*args, object_hook=_object_hook, **kwargs)


def dump(*args, **kwargs):
    return json.dump(cls=PrewikkaJSONEncoder, *args, **kwargs)


def dumps(*args, **kwargs):
    # FIXME: html.escapejson should be removed
    return html.escapejson(json.dumps(cls=PrewikkaJSONEncoder, *args, **kwargs))
