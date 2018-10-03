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


GRAMMAR = r"""
    ?criteria: and
        | criteria "||" and -> or_

    ?and: not
        | and "&&" not -> and_

    ?not: criterion
        | "!" not -> not_

    criterion: path operator value
             | path -> not_null
             | "(" criteria ")" -> parenthesis

    !operator: "=" | "=*" | "==" | "!=" | "!=*" | "<>" | "<>*" | "!<>" | "!<>*" | "<" | "<=" | ">" | ">=" | "~" | "~*" | "!~" | "!~*" -> operator

    int_: DIGIT+
    float_: NUMBER
    path: PATH

    ?value: string
    string: (dqstring | sqstring | uqstring)

    SQSTRING.1: "'" ("\\'" | /[^']/)* "'"
    DQSTRING.1: "\"" ("\\\""|/[^"]/)* "\""
    !sqstring: SQSTRING
    !dqstring: DQSTRING
    !uqstring: UNQUOTED_STRING

    // Normally && and ||
    SPECIAL_CHARACTERS: "&" | "|" | "(" | ")"
    ESCAPED_SPECIAL_CHARACTERS: "\\" SPECIAL_CHARACTERS
    UNQUOTED_STRING.0: (ESCAPED_SPECIAL_CHARACTERS | /[^\s&|()]/)+

    PATH: (PATHELEM ".")* PATHELEM
    PATHELEM: WORD ("(" PATHINDEX ")")?
    PATHINDEX: ("-"? DIGIT+ | DQSTRING | SQSTRING)
    WORD: LETTER (LETTER | DIGIT | "-" | "_")*
    DIGIT: /[0-9]/
    LETTER: /[a-z]/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""
