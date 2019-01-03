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


GRAMMAR = r"""
    ?criteria: criterion
             | criteria (WS|BOOL_AND|BOOL_OR) criterion -> bool_

    criterion: operator field (value | criteria)
             | operator field LPAR criteria RPAR -> parenthesis

    value: (inclusive_range | exclusive_range | value_string)

    inclusive_range: "[" WS* _string WS "TO" WS _string WS* "]"
    exclusive_range: "{" WS* _string WS "TO" WS _string WS* "}"
    value_string: _string (string_modifier)?

    operator: OPERATOR?
    OPERATOR.3: "NOT" WS+ | "!" | "-" | "+"

    _string: (dqstring | sqstring | regstr | uqstring)
    string_modifier: BOOST_MODIFIER | FUZZY_MODIFIER

    BOOST_MODIFIER: "^" /[0-9]+/
    FUZZY_MODIFIER: "~" /[0-9]*/

    SQSTRING.3: "'" ("\\'" | /[^']/)* "'"
    DQSTRING.3: "\"" ("\\\""|/[^"]/)* "\""
    RESTRING.3: "/" ("\\/"|/[^\/]/)* "/"
    !sqstring: SQSTRING
    !dqstring: DQSTRING
    !regstr: RESTRING
    !uqstring: UNQUOTED_STRING

    SPECIAL_CHARACTERS: "+" | "-" | "!" | "(" | ")" | "{" | "}" | "[" | "]" | "^" | "\"" | "~" | "*" | "?" | ":" | "\\" | "&" | "|"
    ESCAPED_SPECIAL_CHARACTERS: "\\" SPECIAL_CHARACTERS
    UNQUOTED_STRING.2: (ESCAPED_SPECIAL_CHARACTERS | /[^+!(){}\[\]^\"\~:\s]/)+

    field: (FIELD)? -> field
    FIELD.2: PATH ":"
    PATH.0: (PATHELEM ".")* PATHELEM
    PATHELEM.0: WORD ("(" PATHINDEX ")")?
    PATHINDEX.0: "-"? (DIGIT+ | UNQUOTED_STRING)
    WORD: LETTER (LETTER | DIGIT | "-" | "_")+
    DIGIT: /[0-9]/
    LETTER: /[a-z]/
    BOOL_AND.1: WS+ ("&&" | "AND") WS+
    BOOL_OR.1: WS+ ("||" | "OR") WS+

    LPAR: WS* "("
    RPAR: WS* ")"

    WS: /[ \t\f\r\n]/+
"""
