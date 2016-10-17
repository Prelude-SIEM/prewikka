# Copyright (C) 2016 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import
import json
import datetime


_TYPES = {}


class _JSONMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        nclass = super(_JSONMetaClass, cls).__new__(cls, clsname, bases, attrs)

        _TYPES[nclass.__name__] = nclass

        return nclass


class JSONObject(object):
    __metaclass__ = _JSONMetaClass

    def __jsonobj__(self):
        return { "__prewikka_class__": (self.__class__.__name__, self.__json__()) }



class PrewikkaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__jsonobj__"):
            return obj.__jsonobj__()

        elif hasattr(obj, "__json__"):
            return obj.__json__()

        elif isinstance(obj, datetime.datetime):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


class PrewikkaJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self._object_hook, *args, **kwargs)

    def _byteify(self, data, ignore_dicts=False):
        if isinstance(data, unicode):
            return data.encode('utf-8')

        elif isinstance(data, list):
            return [self._byteify(item, ignore_dicts=True) for item in data]

        elif isinstance(data, dict) and not ignore_dicts:
            return dict((self._byteify(key, ignore_dicts=True), self._byteify(value, ignore_dicts=True)) for key, value in data.iteritems())

        return data

    def _object_hook(self, obj):
        obj = self._byteify(obj)

        cls = obj.get("__prewikka_class__")
        if cls:
            return _TYPES[cls[0]](*cls[1])

        return obj


def load(*args, **kwargs):
    return json.load(cls=PrewikkaJSONDecoder, *args, **kwargs)


def loads(*args, **kwargs):
    return json.loads(cls=PrewikkaJSONDecoder, *args, **kwargs)


def dump(*args, **kwargs):
    return json.dump(cls=PrewikkaJSONEncoder, *args, **kwargs)


def dumps(*args, **kwargs):
    return json.dumps(cls=PrewikkaJSONEncoder, *args, **kwargs)
