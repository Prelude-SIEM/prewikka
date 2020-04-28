# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
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
import re

from lark import Lark, v_args

from prewikka.dataprovider.parsers.criteria import CommonTransformer
from prewikka.dataprovider import COMPOSITE_TIME_FIELD, DataProviderBase, InvalidPathError
from prewikka.utils import cache

from enum import Enum
from . import grammar


# This regex does not support strings with backslash escaping, i.e. field("a'b\"c").value
STRING_INDEX_REGEX = r"""\((["'])((?:(?!\1).)+)\1\)"""


class SelectionType(Enum):
    PATH = 0
    FUNCTION = 1
    CONSTANT = 2


class _SelectionObject(object):
    type = None

    @property
    def is_path(self):
        return self.type == SelectionType.PATH

    @property
    def is_constant(self):
        return self.type == SelectionType.CONSTANT

    @property
    def is_function(self):
        return self.type == SelectionType.FUNCTION


class _Function(_SelectionObject):
    type = SelectionType.FUNCTION

    def __init__(self, name, args):
        self.name = name
        self.args = args
        self._rtype = {"avg": float, "count": int, "timezone": datetime.datetime}.get(name)

    def get_path(self):
        for i in self.args:
            if isinstance(i, _Path):
                return i
            elif isinstance(i, _Function):
                r = i.get_path()
                if r:
                    return r


class _Path(_SelectionObject):
    _rtype = None
    type = SelectionType.PATH

    def __init__(self, name):
        self.path = name
        self.klass, self.name = name.rsplit(".", 1)
        self.rtype = None

    def __str__(self):
        return self.path


class _Constant(_SelectionObject):
    _rtype = str
    type = SelectionType.CONSTANT

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class SelectionObject(object):
    def __init__(self, obj, extract=[], commands=[]):
        self.object = obj
        self.extract = extract
        self.commands = commands

        self.rtype = int if self.extract else obj._rtype

    def get_path(self):
        if self.object.type == SelectionType.PATH:
            return self.object
        else:
            return self.object.get_path()


class _SelectionTransformer(CommonTransformer):
    def _get_rtype(self, fname):
        return {"avg": float, "count": int, "timezone": datetime.datetime}.get(fname)

    @v_args(inline=True)
    def function_args(self, *args):
        return args

    @v_args(inline=True)
    def function(self, fname, args):
        return _Function(fname, args)

    @v_args(inline=True)
    def path(self, s):
        return _Path(s)

    @v_args(inline=True)
    def const(self, s):
        return _Constant(s)

    @v_args(inline=True)
    def selection(self, data, *args):
        extract = None
        commands = []

        for i in args:
            if i.data == "extract":
                extract = text_type(i.children[0])

            elif i.data == "commands":
                commands = [text_type(j) for j in i.children]

        return SelectionObject(data, extract, commands)


_GRAMMAR = Lark(grammar.GRAMMAR, start="selection", parser="lalr", transformer=_SelectionTransformer())


class PathParser(DataProviderBase):
    def __init__(self, valid_paths, time_field='create_time'):
        DataProviderBase.__init__(self, time_field)

        self.path_types = {}
        self._valid_paths = {}
        self._indexes = {}

        for klass, field in valid_paths.items():
            for name, path_type in field.items():
                public = (name[0] != "_")
                index = False
                if isinstance(path_type, tuple):
                    path_type, index = path_type

                self.register_path("%s.%s" % (klass, name), path_type, public, index)

    def post_load(self):
        DataProviderBase.post_load(self)

        if self._time_field == COMPOSITE_TIME_FIELD:
            # The dataprovider_type attribute is not defined in the __init__ yet
            self.register_path("%s.%s" % (self.dataprovider_type, self._time_field), datetime.datetime, public=False)

    def get_paths(self):
        return sorted(self.path_types.keys())

    def register_path(self, path, path_type, public=True, index=False):
        left_path, key = path.rsplit('.', 1)

        self._valid_paths.setdefault(left_path, {})[key] = path_type
        if public:
            self.path_types[path] = path_type

        if index:
            self._indexes[left_path] = key

    def get_path_type(self, path):
        try:
            return self.path_types[self.unindex_path(path)]
        except KeyError:
            raise InvalidPathError(path)

    @staticmethod
    def unindex_path(path):
        return re.sub(STRING_INDEX_REGEX, "", path)

    def _check_path(self, klass, attribute):
        # Handle functions without an actual path, eg. "count(1)".
        if klass is None and attribute is None:
            return

        if attribute not in self._valid_paths.get(self.unindex_path(klass), {}):
            raise InvalidPathError("%s.%s" % (klass, attribute))

    def _get_path_rtype(self, selection, path):
        rtype = selection.rtype
        if rtype:
            return rtype

        return self._valid_paths[path.klass][path.name]

    @cache.request_memoize("pathparser")
    def _parse_path(self, path):
        selection = _GRAMMAR.parse(path)

        path = selection.get_path()
        if path:
            self._check_path(path.klass, path.name)
            return selection, self._get_path_rtype(selection, path)
        else:
            return selection, selection.rtype

    def parse_paths(self, paths):
        parsed_paths = []
        types = []

        for path in paths:
            parsed_path, rtype = self._parse_path(path)

            types.append(rtype)
            parsed_paths.append(parsed_path)

        return parsed_paths, types

    def compile_criterion(self, criterion):
        left_path, key = criterion.left.rsplit('.', 1)
        self._check_path(left_path, key)

        return criterion

    def get_indexation_path(self, path):
        # Handle path indexation by string
        klass = self.unindex_path(path).rsplit('.', 1)[0]
        try:
            return "%s.%s" % (klass, self._indexes[klass])
        except KeyError:
            raise InvalidPathError(path)
