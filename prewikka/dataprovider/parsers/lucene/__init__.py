# Copyright (C) 2018-2019 CS-SI. All Rights Reserved.
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
from prewikka.dataprovider import Criterion, ParserError

from . import grammar


_grammar = Lark(grammar.GRAMMAR, start="criteria", parser="lalr", keep_all_tokens=True)


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
            # We modify the internal value representation, directly accessed from value_string()
            s.value = r[1]
            op = "~"
        else:
            op = "<>*"

        return op, s

    string = v_args(inline=True)(lambda _, s: s)
    sqstring = v_args(inline=True)(lambda _, s: ("<>*", CommonTransformer._hack(s, "'")))
    dqstring = v_args(inline=True)(lambda _, s: ("<>*", CommonTransformer._hack(s, '"')))
    regstr = v_args(inline=True)(lambda _, s: ("~", CommonTransformer._hack(s, '/')))


class CriteriaTransformer(CommonTransformer):
    def __init__(self, compile=Criterion, default_paths=[]):
        self._compile = compile
        self._default_paths = default_paths

    def string_modifier(self, data):
        raise LuceneEmulationError

    @v_args(inline=True)
    def operator(self, data=None):
        if data == "+":
            raise LuceneEmulationError

        return data

    def _get_value_operator(self, t, parent_operator, parent_field):
        op, value = t
        if parent_operator in ("-", "!", "NOT"):
            op = "!" + op

        return value.value, op

    def _get_fields(self, parent_field):
        return [parent_field] if parent_field else self._default_paths

    def _range(self, parent_field, from_, to, op_a, op_b):
        fields = self._get_fields(parent_field)
        return functools.reduce(lambda x, y: x | y, (self._compile(path, op_a, from_) & self._compile(path, op_b, to) for path in fields), Criterion())

    def _tree_to_criteria(self, t, parent_operator=None, parent_field=[]):
        tag = getattr(t, "data", None)
        if not tag:
            return text_type(t.value) if t else None

        if tag == "bool_":
            if "AND" in t.children[1] or "&&" in t.children[1]:
                op = "&&"
            else:
                op = "||"

            return Criterion(self._tree_to_criteria(t.children[0], parent_operator, parent_field), op, self._tree_to_criteria(t.children[2], parent_operator, parent_field))

        elif tag == "field":
            return t.children[0][:-1] if t.children else None

        elif tag == "criterion":
            operator, field, value = t.children
            return self._tree_to_criteria(value, self._tree_to_criteria(operator) or parent_operator, self._tree_to_criteria(field) or parent_field)

        elif tag == "parenthesis":
            operator, field, _, data, _ = t.children
            return self._tree_to_criteria(data, self._tree_to_criteria(operator) or parent_operator, self._tree_to_criteria(field) or parent_field)

        elif tag == "value_string":
            value, op = self._get_value_operator(t.children[0], parent_operator, parent_field)

            ret = Criterion()
            for i in self._get_fields(parent_field):
                ret |= self._compile(i, op, value)

            return ret

        elif tag == "inclusive_range":
            from_, to = filter(lambda x: isinstance(x, tuple), t.children)
            if parent_operator not in ("-", "!", "NOT"):
                ret = self._range(parent_field, from_[1], to[1], ">=", "<=")
            else:
                ret = self._range(parent_field, from_[1], to[1], "<=", ">=")

            return ret

        elif tag == "exclusive_range":
            from_, to = filter(lambda x: isinstance(x, tuple), t.children)
            if parent_operator not in ("-", "!", "NOT"):
                ret = self._range(parent_field, from_[1], to[1], ">", "<")
            else:
                ret = self._range(parent_field, from_[1], to[1], "<", ">")

            return ret

        elif t.children:
            return self._tree_to_criteria(t.children[0], parent_operator, parent_field)

    def transform(self, tree):
        return self._tree_to_criteria(Transformer.transform(self, tree))


class ReconstructTransformer(CommonTransformer):
    def _value_string(self, vl, field=None):
        return vl[1]

    def _tree_tostring(self, t, parent_field=None):
        tag = getattr(t, "data", None)

        if tag == "value_string":
            return self._value_string(t.children[0], parent_field)

        if not tag:
            if isinstance(t, tuple):
                return text_type(t[1])

            return text_type(t)

        elif tag == "criterion":
            operator, field, value = t.children
            operator = self._tree_tostring(operator)
            field = self._tree_tostring(field)
            value = self._tree_tostring(value, field or parent_field)
            return "".join([operator, field, value])

        elif tag == "parenthesis":
            operator, field, lp, value, rp = t.children
            operator = self._tree_tostring(operator)
            field = self._tree_tostring(field)
            value = self._tree_tostring(value, field or parent_field)
            return "".join([operator, field, lp, value, rp])

        else:
            return "".join(self._tree_tostring(i, parent_field) for i in t.children)

        return ""

    def transform(self, tree):
        return self._tree_tostring(Transformer.transform(self, tree))


def parse(input, transformer=None):
    """Convert a Lucene string to a Criterion object."""
    try:
        tree = _grammar.parse(input)
    except LarkError as e:
        raise ParserError(details=e)

    if transformer:
        return transformer.transform(tree)

    return tree
