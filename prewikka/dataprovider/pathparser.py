# -*- coding: utf-8 -*-
# Copyright (C) 2016-2018 CS-SI. All Rights Reserved.
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

from prewikka.dataprovider import Criterion, DataProviderBase, InvalidCriterionError, InvalidPathError
from prewikka.utils import cache

from ometa.runtime import ParseError

import datetime
import functools
import parsley

from . import grammar


_grammar = parsley.makeGrammar(grammar.GRAMMAR, {
    "datetime": datetime,
    "functools": functools
})


class PathParser(DataProviderBase):
    def __init__(self, valid_paths, time_field='create_time', type=None):
        DataProviderBase.__init__(self, time_field)

        self.path_types = {}
        self._valid_paths = {}

        for klass, field in valid_paths.items():
            for name, path_type in field.items():
                public = True
                if isinstance(path_type, tuple):
                    path_type, public = path_type

                self.register_path("%s.%s" % (klass, name), path_type, public)

    def get_paths(self):
        return sorted(self.path_types.keys())

    def register_path(self, path, path_type, public=True):
        left_path, key = path.rsplit('.', 1)

        self._valid_paths.setdefault(left_path, {})[key] = path_type
        if public:
            self.path_types[path] = path_type

    def get_path_type(self, path):
        try:
            return self.path_types[path]
        except KeyError:
            raise InvalidPathError(path)

    def _check_path(self, klass, attribute):
        # Handle functions without an actual path, eg. "count(1)".
        if klass is None and attribute is None:
            return

        if klass not in self._valid_paths or attribute not in self._valid_paths[klass]:
            raise InvalidPathError("%s.%s" % (klass, attribute))

    def _get_path_rtype(self, parsed_path):
        rtype = parsed_path["rtype"]
        if rtype:
            return rtype

        klass = parsed_path["attribute_info"]["klass"]
        attribute = parsed_path["attribute_info"]["name"]
        return self._valid_paths[klass][attribute]

    @cache.request_memoize("pathparser")
    def _parse_path(self, path):
        parsed_path = _grammar(path).selection()

        self._check_path(parsed_path["path"]["attribute_info"]["klass"],
                         parsed_path["path"]["attribute_info"]["name"])

        return parsed_path, self._get_path_rtype(parsed_path["path"])

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


def string_to_criterion(criteria, compile=Criterion):
    """Convert a string to a Criterion object."""
    try:
        return _grammar(criteria).criteria(compile)
    except ParseError:
        raise InvalidCriterionError
