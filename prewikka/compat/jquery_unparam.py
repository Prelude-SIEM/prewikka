#!/usr/bin/python
# -*- coding: utf-8 -*-

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


def parse_key_pair(keyval, unquote=False):
    keyval_splitted = keyval.split('=', 1)
    if len(keyval_splitted) == 1:
        key, val = keyval_splitted[0], ''
    else:
        key, val = keyval_splitted

    if key == '' or val == '':
        return {}

    if unquote:
        key = unquote_plus(key)
        val = unquote_plus(val)

    if not Py3:
        key = key.decode("utf8")
        val = val.decode("utf8")

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
        return None

    if len(structs) == 1:
        return structs[0]

    first, rest = structs[0], structs[1:]
    return merge_two_structs(first, merge_structs(rest))


def _unparam(jquery_params, unquote=True):
    pair_strings = jquery_params.split('&')
    key_pairs = [parse_key_pair(x, unquote) for x in pair_strings]
    return merge_structs(key_pairs)


def jquery_unparam_unquoted(jquery_params):
    return _unparam(jquery_params, unquote=False)


def jquery_unparam(jquery_params):
    return _unparam(jquery_params, unquote=True)
