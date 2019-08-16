#!/usr/bin/python
# -*- coding: utf-8 -*-

import functools
import re
import sys

try:
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import unquote_plus

if sys.version_info >= (3, 0):
    Py3 = True
else:
    Py3 = False


def _decode(string, unquote=False):
    if unquote:
        string = unquote_plus(string)

    if not Py3:
        string = string.decode("utf8")

    return string


def parse_key_pair(keyval, unquote=False):
    keyval_splitted = keyval.split('=', 1)
    if len(keyval_splitted) == 1:
        key, val = keyval_splitted[0], ''
    else:
        key, val = keyval_splitted

    return _decode(key, unquote), _decode(val, unquote)


def build_struct(key, val):
    if key == '' or val == '':
        return {}

    groups = re.findall(r"\[.*?\]", key)
    groups_joined = ''.join(groups)
    if key[-len(groups_joined):] == groups_joined:
        key = key[:-len(groups_joined)]
        for group in reversed(groups):
            if group == '[]':
                val = [val]
            else:
                val = {group[1:-1]: val}

    return {key: val}


def merge_two_structs(s1, s2):
    if isinstance(s1, list) and isinstance(s2, list):
        return s1 + s2

    if isinstance(s1, dict) and \
       isinstance(s2, dict):

        retval = s1.copy()

        for key, val in s2.items():
            if retval.get(key) is None:
                retval[key] = val
            else:
                retval[key] = merge_two_structs(retval[key], val)
        return retval
    return s2


def merge_structs(structs):
    if len(structs) == 0:
        return {}

    return functools.reduce(lambda x, y: merge_two_structs(y, x), reversed(structs))


def handle_indexes(s, toplevel=False):
    if isinstance(s, list):
        return [handle_indexes(item) for item in s]

    if isinstance(s, dict):
        if not toplevel and s and all(k.isdigit() for k in s.keys()):
            return [handle_indexes(v) for k, v in sorted(s.items(), key=lambda x: int(x[0]))]
        else:
            return {k: handle_indexes(v) for k, v in s.items()}

    return s


def jquery_unparam(jquery_params, unquote=True, multipart=False):
    if multipart:
        params = [(_decode(k, unquote), v) for k, v in jquery_params]
    else:
        params = [parse_key_pair(x, unquote) for x in jquery_params.split('&')]

    structs = [build_struct(k, v) for k, v in params]
    return handle_indexes(merge_structs(structs), toplevel=True)
