# coding: utf-8
# Copyright (C) 2019-2020 CS-SI. All Rights Reserved.
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
    selection: (function | path) [extract] [commands]

    extract: ":" EXTRACT
    commands: "/" COMMAND ("," COMMAND)*

    ?function: FUNCTION "(" function_args ")"
    function_args: _function_arg ("," _function_arg)*
    _function_arg: path | function | const

    COMMAND: "group_by" | "order_desc" | "order_asc"
    EXTRACT: "year" | "month" | "yday" | "mday" | "wday" | "hour" | "min" | "sec" | "msec" | "usec" | "quarter"
    FUNCTION.2: "count" | "min" | "max" | "sum" | "avg" | "timezone" | "distinct"

    int_: DIGIT
    float_: NUMBER
    path: PATH
    const: DIGIT | NUMBER | string
    string: (dqstring | sqstring)

    SQSTRING.1: "'" ("\\'" | /[^']/)* "'"
    DQSTRING.1: "\"" ("\\\""|/[^"]/)* "\""
    !sqstring: SQSTRING
    !dqstring: DQSTRING

    PATH.1: (PATHELEM ".")* PATHELEM
    PATHELEM: WORD ("(" PATHINDEX ")")?
    PATHINDEX: ("-"? DIGIT+ | DQSTRING | SQSTRING)
    WORD: (LETTER | "_") (LETTER | DIGIT | "-" | "_")*
    DIGIT: /[0-9]/+
    LETTER: /[a-z]/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""
