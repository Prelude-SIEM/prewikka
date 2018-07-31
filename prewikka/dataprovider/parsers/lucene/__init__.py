# Copyright (C) 2018 CS-SI. All Rights Reserved.
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

import functools
import re

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError

from prewikka import error
from prewikka.dataprovider import Criterion, InvalidCriterionError

from . import grammar


_grammar = Lark(grammar.GRAMMAR, start="criteria", parser="lalr")


def _wildcard_to_regex(value):
    ret = ""
    lst = re.split("([*?])", value)
    for part in lst:
        if part == "*":
            ret += ".*"
        elif part == "?":
            ret += "."
        else:
            ret += re.escape(part)

    return len(lst), ret


class LuceneEmulationError(error.PrewikkaUserError):
    name = N_("Lucene emulation error")
    message = N_("This Lucene expression cannot be emulated properly using the Criterion backend")


class CommonTransformer(Transformer):
    @staticmethod
    def _unescape(input, escaped):
        return input.replace('\\%s' % escaped, escaped)

    @staticmethod
    def _hack(s, escaped):
        # We modify the internal value representation, directly accessed from value_string()
        s.value = CommonTransformer._unescape(s[1:-1], escaped)
        return s

    @v_args(inline=True)
    def uqstring(self, s):
        r = _wildcard_to_regex(s)
        if r[0] > 1:
            self._operator = "~"

            # We modify the internal value representation, directly accessed from value_string()
            s.value = r[1]

        return s

    string = v_args(inline=True)(lambda _, s: s)
    sqstring = v_args(inline=True)(lambda _, s: CommonTransformer._hack(s, "'"))
    dqstring = v_args(inline=True)(lambda _, s: CommonTransformer._hack(s, '"'))


class CriteriaTransformer(CommonTransformer):
    _attrlst = ["_operator"]

    def _reset(self):
        for i in self._attrlst:
            setattr(self, i, None)

    def __init__(self, compile=Criterion, default_paths=[]):
        self._compile = compile
        self._default_paths = default_paths
        self._bool_operator = None
        self._reset()

    @v_args(inline=True)
    def regstr(self, s):
        self._operator = "~"
        return self._hack(s, "/")

    def string_modifier(self, s):
        raise LuceneEmulationError

    @v_args(inline=True)
    def field(self, s=None):
        return [s[0:-1]] if s else None

    @v_args(inline=True)
    def value_string(self, field, value, modifier=None):
        op = self._operator or "="
        if not field:
            op = self._operator or "<>*"
            field = self._default_paths

        return functools.reduce(lambda x, y: x | y, (self._compile(path, op, value.value) for path in field), Criterion())

    def _range(self, fields, from_, to, op_a, op_b):
        return functools.reduce(lambda x, y: x | y, (self._compile(path, op_a, from_) & self._compile(path, op_b, to) for path in fields), Criterion())

    @v_args(inline=True)
    def inclusive_range(self, field, from_, to):
        if not field:
            field = self._default_paths

        if self._operator not in ("NOT ", "-", "!"):
            return self._range(field, from_, to, ">=", "<=")
        else:
            return self._range(field, from_, to, "<=", ">=")

    @v_args(inline=True)
    def exclusive_range(self, field, from_, to):
        if not field:
            field = self._default_paths

        if self._operator not in ("NOT ", "-", "!"):
            return self._range(field, from_, to, ">", "<")
        else:
            return self._range(field, from_, to, "<", ">")

    @v_args(inline=True)
    def criterion(self, operator, crit):
        if operator in ("NOT ", "-"):
            crit.operator = "!=" if crit.operator == "==" else "!" + crit.operator

        elif operator == "+":
            raise LuceneEmulationError

        return crit

    def bool_(self, s):
        if len(s) == 3:
            left, op, right = s
        else:
            op = "||"
            left, right = s

        ret = Criterion(left, self._bool_operator or {"AND": "&&", "OR": "||"}.get(op, "||"), right)
        self._bool_operator = None
        return ret

    operator = v_args(inline=True)(text_type)
    parenthesis = v_args(inline=False)(lambda s, x: x[1])
    or_ = v_args(inline=True)(lambda _, left, right: Criterion(left, "||", right))
    and_ = v_args(inline=True)(lambda _, left, right: Criterion(left, "&&", right))


class ReconstructTransformer(CommonTransformer):
    def _tree_tostring(self, t):
        tag = getattr(t, "data", None)
        if not tag:
            return text_type(t)

        elif tag == "bool_" and len(t.children) == 2:
            return "%s %s" % tuple(self._tree_tostring(i) for i in t.children)

        elif tag == "inclusive_range":
            return "%s[%s TO %s]" % tuple(self._tree_tostring(i) for i in t.children)

        elif tag == "exclusive_range":
            return "%s{%s TO %s}" % tuple(self._tree_tostring(i) for i in t.children)

        else:
            return "".join(self._tree_tostring(i) for i in t.children)

        return ""

    def transform(self, tree):
        return self._tree_tostring(Transformer.transform(self, tree))


def parse(input, transformer=None):
    """Convert a Lucene string to a Criterion object."""
    try:
        tree = _grammar.parse(input)
    except LarkError:
        raise InvalidCriterionError

    if transformer:
        return transformer.transform(tree)

    return tree
