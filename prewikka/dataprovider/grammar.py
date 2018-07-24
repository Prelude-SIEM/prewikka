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


GRAMMAR = r"""
GROUP_BY_CMD = 'group_by'
ORDER_BY_CMD = 'order_desc' | 'order_asc'
COMMAND = (GROUP_BY_CMD | ORDER_BY_CMD):cmd -> cmd

COMMANDS = COMMAND:first (',' COMMAND)*:rest -> [first] + rest

EXTRACT = 'year' | 'month' | 'yday' | 'mday' | 'wday' | 'hour' | 'min' | 'sec' | 'msec' | 'usec' | 'quarter'

FUNCTION = 'count':f -> {"rtype": int, "name": f}
           | 'min':f -> {"rtype": None, "name": f}
           | 'max':f -> {"rtype": None, "name": f}
           | 'sum':f -> {"rtype": None, "name": f}
           | 'avg':f -> {"rtype": float, "name": f}
           | 'timezone':f -> {"rtype": datetime.datetime, "name": f}

CMP_OPERATOR = '==' | '=*' | '!=*' | '!='
               | '<=' | '>='
               | '<>*' | '!<>*'| '<>' | '!<>'
               | '<' | '>'
               | '~*' | '~' | '!~*' | '!~'
               | '=' -> '=='

XDIGIT = :x ?(x in '0123456789abcdefABCDEF') -> x
EXPONENT = ('e' | 'E') ('+' | '-')? <digit+>
floatPart :sign :ds = <('.' <digit+> EXPONENT?) | EXPONENT>:tail -> float(sign + ds + tail)
intfloat = ('-' | -> ''):sign (<digit+>:ds (floatPart(sign ds) | -> int(sign + ds)))

escapedChar = '\\' (('"' -> '"') | ('\\' -> '\\')
               | ('/' -> '/')    | ('b' -> '\b')
               | ('f' -> '\f')   | ('n' -> '\n')
               | ('r' -> '\r')   | ('t' -> '\t')
               | ('\'' -> '\'')  | escapedUnicode)
escapedUnicode = 'u' <XDIGIT{4}>:hs -> unichr(int(hs, 16))
string = '"' (escapedChar | ~'"' anything)*:c '"' -> ''.join(c)
        | "'" (escapedChar | ~"'" anything)*:c "'" -> ''.join(c)

word = <(letterOrDigit|'-'|'_')+>
pathindex = intfloat|string
pathelem = <word ('(' pathindex ')')?>
field = (<(pathelem'.')+>:t pathelem:col) (('[' string:s ']') -> s)?:k -> {"klass": t.rstrip('.'), "name": col, "key":k}

function_arg = string | intfloat
function_args = function_arg:first (',' ws function_arg)*:rest -> [first] + rest

# For the time being, the first argument of the function should be a field.
# Other arguments of type string, float or integer can be added.

# FIXME: count(distinct) is a separate case, as we don't support imbricated functions.
# We probably should use count_distinct at the dataprovider level (including libpreludedb).

path = FUNCTION:func '(' ws field:fi (ws ',' ws function_args:args -> args)?:args ws ')' -> {"function": {"name": func["name"], "args": args or []},
                                                                                             "rtype": func["rtype"],
                                                                                             "attribute_info": fi}
       | 'count(distinct(' ws field:fi ws '))' -> {"function": {"name": "count_distinct", "args": []}, "rtype": int, "attribute_info": fi}
       | field:fi -> {"attribute_info": fi, "rtype": None}

criterion_path = <(<(pathelem'.')*> pathelem) ('[' string ']')?>

function_constant = FUNCTION:func '(' <digit+>:ds ')' -> {"function": {"name": func["name"], "args": []},
                                                             "rtype": func["rtype"],
                                                             "attribute_info": {"klass": None, "name": None, "key": int(ds, 10)}}

selection_path = path:p (':' EXTRACT:ex -> ex)?:ex ('/' COMMANDS:cmds -> cmds)?:cmds -> {"path": p if not ex else dict(p, rtype=int),
                                                                                         "commands": cmds or [],
                                                                                         "extract": ex
                                                                                         }
selection_func_constant = function_constant:fc (':' EXTRACT:ex -> ex)?:ex ('/' ORDER_BY_CMD:cmd -> cmd)?:cmd -> {"path": fc, "commands": [cmd], "extract": ex}
selection =   selection_path:p -> p
            | selection_func_constant:fc -> fc

noseparator = anything:x ?(x not in '&|()\t\n\x0b\x0c\r ') -> x
unquoted_string = (noseparator)+:c -> ''.join(c)

operand = ((intfloat:i ~noseparator -> i) | string | unquoted_string):opd -> opd

criterion :compile = (criterion_path:l ws CMP_OPERATOR:op ws operand:r) -> compile(l, op, r)
            | criterion_path:l -> compile(l, '!=', None)
            | '!' criterion_path:l -> compile(l, '==', None)


logical_and :compile = ws "&&" ws exp_value(compile):v    -> v
logical_or :compile  = ws "||" ws expression(compile):e   -> e

parens :compile      = '(' ws criteria(compile):e ws ')'  -> e
exp_value :compile   = parens(compile) | criterion(compile)

criteria :compile = expression(compile):left logical_or(compile)*:right -> functools.reduce(lambda x, y: x | y, [left] + right)
expression :compile  = exp_value(compile):left logical_and(compile)*:right -> functools.reduce(lambda x, y: x & y, [left] + right)
"""
