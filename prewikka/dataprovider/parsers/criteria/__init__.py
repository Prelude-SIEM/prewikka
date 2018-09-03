# Copyright (C) 2018 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannvg@gmail.com>
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

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError

from prewikka.dataprovider import Criterion, InvalidCriterionError

from . import grammar


_grammar = Lark(grammar.GRAMMAR, start="criteria", parser="lalr")


class CommonTransformer(Transformer):
    @staticmethod
    def _unescape(input, escaped):
        return input.replace('\\%s' % escaped, escaped)

    @v_args(inline=True)
    def dqstring(self, s):
        s.value = self._unescape(s.value[1:-1], '"')
        return s.value

    @v_args(inline=True)
    def sqstring(self, s):
        s.value = self._unescape(s.value[1:-1], "'")
        return s.value

    uqstring = v_args(inline=True)(text_type)
    path = string = operator = v_args(inline=True)(text_type)


class CriteriaTransformer(CommonTransformer):
    def __init__(self, compile=Criterion):
        self._compile = compile

    parenthesis = v_args(inline=True)(lambda self, criterion: criterion)
    or_ = v_args(inline=True)(lambda self, left, right: Criterion(left, "||", right))
    and_ = v_args(inline=True)(lambda self, left, right: Criterion(left, "&&", right))
    criterion = v_args(inline=True)(lambda self, left, op, right: self._compile(left, op, right))


def parse(input, transformer=CriteriaTransformer()):
    """Convert a Criterion string to a Criterion object."""
    try:
        tree = _grammar.parse(input)
    except LarkError:
        raise InvalidCriterionError

    if transformer:
        return transformer.transform(tree)

    return tree
