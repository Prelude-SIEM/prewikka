# Copyright (C) 2018 CS-SI. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

import functools
import parsley
import re

from ometa.runtime import ParseError

from prewikka.dataprovider import Criterion, InvalidCriterionError
from prewikka import utils

from . import grammar


def wildcard_to_regex(value):
    ret = ""
    for part in re.split("([*?])", value):
        if part == "*":
            ret += ".*"
        elif part == "?":
            ret += "."
        else:
            ret += re.escape(part)

    return ret


def criterion(params, field, operator, value, negate):
    if not field:
        return functools.reduce(lambda x, y: x | y, (criterion(params, path, operator, value, negate) for path in params.default_paths), Criterion())

    return params.compile(field, "!%s" % operator if negate else operator, value)


def range_criterion(params, field, range_, negate):
    inf, sup = range_
    if not negate:
        return params.compile(field, ">=", inf) & params.compile(field, "<=", sup)
    else:
        return params.compile(field, "<", inf) | params.compile(field, ">", sup)


_grammar = parsley.makeGrammar(grammar.GRAMMAR, {
    'functools': functools,
    'criterion': criterion,
    'range_criterion': range_criterion,
    'wildcard_to_regex': wildcard_to_regex
})


def lucene_to_criterion(criteria, compile=Criterion, default_paths=[]):
    """Convert a Lucene string to a Criterion object."""
    try:
        return _grammar(criteria).criteria(utils.AttrObj(compile=compile, default_paths=default_paths))
    except ParseError:
        raise InvalidCriterionError
