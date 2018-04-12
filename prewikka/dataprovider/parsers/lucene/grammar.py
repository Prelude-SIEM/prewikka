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


# TODO: support boosting and fuzziness (by ignoring them), as well as exclusive ranges

GRAMMAR = r"""
space = (anything:x ?(x.isspace()))+
word = letter (letterOrDigit|'-'|'_')*
index = '-'? digit+
pathelem = word ('(' index ')')?
field = <(pathelem '.')* pathelem>

string = '"' (('\\"' -> '"') | ~'"' anything)*:c '"' -> ''.join(c)
regex = '/' (('\\/' -> '/') | ~'/' anything)*:c '/' -> ''.join(c)

special = anything:x ?(x in '()[]{}:+-*?!&|^~') -> x
escaped_special = '\\' special:x -> x

string_char = escaped_special | ~special anything:x ?(not x.isspace()) -> x
wildcard_string_char = string_char | '*' | '?'

unquoted_wildcard_string = wildcard_string_char+:c -> ''.join(c)
unquoted_string = string_char+:c ~wildcard_string_char -> ''.join(c)

value = string:s -> ('=', s)
        | regex:r -> ('~', r)
        | unquoted_string:s -> ('=', s)
        | unquoted_wildcard_string:w -> ('~', wildcard_to_regex(w))
negate = 'NOT' space -> True
         | '-' -> True
         | '+' -> False
range = '[' ws unquoted_string:inf space 'TO' space unquoted_string:sup ws ']' -> (inf, sup)

criterion :params = negate?:n field:f ws ':' ws range:r -> range_criterion(params, f, r, n)
                    | negate?:n (field:f ws ':' ws -> f)?:fi value:v -> criterion(params, fi, v[0] if fi else '<>*', v[1], n)

logical_and :params = space ('AND' | '&&') space exp_value(params):v -> v
                      | space exp_value(params):v -> v
logical_or :params = space ('OR' | '||') space expression(params):e -> e

parens :params = '(' ws criteria(params):e ws ')' -> e
exp_value :params = parens(params) | criterion(params)

criteria :params = expression(params):left logical_and(params)*:right -> functools.reduce(lambda x, y: x & y, [left] + right)
expression :params = exp_value(params):left logical_or(params)*:right -> functools.reduce(lambda x, y: x | y, [left] + right)
"""
