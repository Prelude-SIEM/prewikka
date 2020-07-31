# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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


_grammar = Lark(grammar.GRAMMAR, start="input", parser="lalr", keep_all_tokens=True)


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


class _CustomCriterion(object):
    def __init__(self, c):
        self.criterion = c


class _Required(_CustomCriterion):
    pass


class _Optional(_CustomCriterion):
    pass


# From http://lucene.472066.n3.nabble.com/operator-precedence-and-confusing-result-td642263.html:
#
# Lucene's query model is based on REQUIRED, OPTIONAL, and EXCLUDED
# clauses.  A clause with no annotation is always OPTIONAL, and doesn't
# affect matching unless there are only OPTIONAL clauses on that level.
# brackets () create a subclause (note that this is OPTIONAL by
# default!).  AND terms are translated into REQUIRED clauses, AND NOT's
# are translated into EXCLUDED clauses.  Require clauses are annotated
# with +'s
#
# A AND B OR C OR D OR E OR F
# -> +A +B C D E F
# -> find documents that match clause A and clause B (other clauses
# don't affect matching)
#
# C OR D OR E OR F
# -> C D E F
# -> find documents matching at least one of these clauses
#
# A AND (B OR C OR D OR E OR F)
# -> +A +(B C D E F)
# -> find documents that match A, and match one of B, C, D, E, or F
#
# (A AND B) OR C OR D OR E OR F
# -> (+A +B) C D E F
# -> find documents that match at least one of C, D, E, F, or both of A
# and B
#
# The key takeaway: once you have an AND in a grouped set of clauses,
# the OR are completely irrelevant for matching.
#
class CriteriaTransformer(CommonTransformer):
    def __init__(self, compile=Criterion, default_paths=[]):
        self._compile = compile
        self._default_paths = default_paths

    def string_modifier(self, data):
        raise LuceneEmulationError

    def _get_fields(self, parent_field):
        return [parent_field] if parent_field else self._default_paths

    def _range(self, parent_field, from_, to, op_a, op_b):
        fields = self._get_fields(parent_field)
        return functools.reduce(lambda x, y: x | y, (self._compile(path, op_a, from_) & self._compile(path, op_b, to) for path in fields), Criterion())

    def _get_criterion(self, data, field, parent_field):
        obj = self._tree_to_criteria(data, self._tree_to_criteria(field) or parent_field)
        if not isinstance(obj, Criterion):
            return obj.criterion

        return obj

    def _bool(self, a, op, b, parent_field=[]):
        a = self._tree_to_criteria(a, parent_field)
        b = self._tree_to_criteria(b, parent_field)
        if b is None or (isinstance(a, _Required) and isinstance(b, _Optional)):
            return a

        elif a is None or (isinstance(b, _Required) and isinstance(a, _Optional)):
            return b

        else:
            return a.__class__(Criterion(a.criterion, "&&" if isinstance(a, _Required) else op, b.criterion))

    def _tree_to_criteria(self, t, parent_field=[], has_required=False):
        tag = getattr(t, "data", None)
        if not tag:
            return text_type(t.value) if t else None

        if tag == "or_":
            return self._bool(t.children[0], "||", t.children[2], parent_field)

        elif tag == "and_":
            return self._bool(t.children[0], "&&", t.children[2], parent_field)

        elif tag == "field" and t.children:
            return t.children[0].replace(" ", "")[:-1]

        elif tag == "parenthesis":
            _, data, _ = t.children
            return self._tree_to_criteria(data, parent_field).criterion

        elif tag == "value_string":
            op, value = t.children[0]

            ret = Criterion()
            for i in self._get_fields(parent_field):
                if i.endswith(".exact"):
                    i = i[:-6:]
                    op = "=="

                ret |= self._compile(i, op, value.value)

            return ret

        elif tag == "inclusive_range":
            from_, to = filter(lambda x: isinstance(x, tuple), t.children)
            return self._range(parent_field, from_[1], to[1], ">=", "<=")

        elif tag == "exclusive_range":
            from_, to = filter(lambda x: isinstance(x, tuple), t.children)
            return self._range(parent_field, from_[1], to[1], ">", "<")

        elif tag in "required":
            if len(t.children) > 1:
                _, field, data = t.children
                return _Required(self._get_criterion(data, field, parent_field))

        elif tag == "excluded":
            if len(t.children) > 1:
                _, field, data = t.children
                return _Required(Criterion(operator="!", right=self._get_criterion(data, field, parent_field)))

        elif tag == "optional":
            field, data = t.children
            return _Optional(self._get_criterion(data, field, parent_field))

        elif tag == "input":
            return self._tree_to_criteria(t.children[1], parent_field)

        elif t.children:
            return self._tree_to_criteria(t.children[0], parent_field)

    def transform(self, tree):
        return self._tree_to_criteria(Transformer.transform(self, tree)).criterion


class ReconstructTransformer(CommonTransformer):
    def _value_string(self, vl, field=None):
        return vl[1]

    def _tree_tostring(self, t, parent_field=None):
        tag = getattr(t, "data", None)

        if tag == "value_string":
            return self._value_string(t.children[0], parent_field)

        elif tag in ("required", "excluded"):
            if len(t.children) == 1:
                return self._tree_tostring(t.children[0])

            operator, field, value = t.children
            field = self._tree_tostring(field)
            return "".join([self._tree_tostring(operator), field, self._tree_tostring(value, field or parent_field)])

        elif tag == "optional":
            field, value = t.children
            field = self._tree_tostring(field)
            return "".join([field, self._tree_tostring(value, field or parent_field)])

        if not tag:
            if isinstance(t, tuple):
                return text_type(t[1])

            return text_type(t)

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
