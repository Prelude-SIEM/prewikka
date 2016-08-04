# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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

import os.path
import time
import sys
import re
import struct
import json
import datetime

from prewikka import compat, env

port_dict = {}
read_done = False

# FIXME: Need appropriate implementation
def get_analyzer_status_from_latest_heartbeat(heartbeat, error_margin):
    if heartbeat.get("additional_data('Analyzer status').data") == ("exiting",):
        return "offline", _("Offline")

    if heartbeat.get("heartbeat_interval") is None:
        return "unknown", _("Unknown")

    if time.time() - int(heartbeat.get("create_time")) > int(heartbeat.get("heartbeat_interval")) + error_margin:
        return "missing", _("Missing")

    return "online", _("Online")


def _load_protocol():
    global port_dict
    global read_done

    if read_done:
        return port_dict

    read_done = True
    sreg = re.compile("^\s*(?P<name>[^#]\w+)\s*(?P<number>\d+)\s*(?P<alias>\w+)")

    try: fd = open("/etc/protocols", "r")
    except IOError:
        return port_dict

    for line in fd.readlines():

        ret = sreg.match(line)
        if not ret:
            continue

        name, number, alias = ret.group("name", "number", "alias")
        port_dict[int(number)] = (name, alias)

    return port_dict


def protocol_number_to_name(num):
     port_dict = _load_protocol()

     if port_dict.has_key(num):
         return port_dict[num][0]

     return None

def nameToPath(name):
    if not isinstance(name, compat.STRING_TYPES):
        name = str(name)

    return name.lower().replace(" ", "_")

def escape_attribute(value):
    if not isinstance(value, compat.STRING_TYPES):
        value = str(value)

    # Escape '\' since it's a valid js escape.
    return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("/", "\\/")

def escape_criteria(criteria):
    if not isinstance(criteria, compat.STRING_TYPES):
        criteria = str(criteria)

    return criteria.replace("\\", "\\\\").replace("'", "\\'")


def property(type, name, parameter, value=None):
    return { "type": type, "name": name, "parameter": parameter, "value": value }


def text_property(name, parameter, value=None):
    return property("text", name, parameter, value)


def password_property(name, parameter):
    return property("password", name, parameter)


def boolean_property(name, parameter, value=False):
    return property("checkbox", name, parameter, value)


def escape_html_string(s):
    if not isinstance(s, compat.STRING_TYPES):
        s = str(s)

    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&#39;")
    return s


def find_unescaped_characters(value, characters=None):
    """Search for unescaped characters among *characters* in string *value*."""
    escaped = False
    if not characters:
        return False

    for char in value:
        if escaped:
            escaped = False
        elif char in characters:
            return True
        elif char == '\\':
            escaped = True

    return False


def split_unescaped_characters(value, characters):
    """Split the string *value* using unescaped *characters* as delimiters."""
    escaped = False
    start = 0

    for index, char in enumerate(value):
        if escaped:
            escaped = False
        elif char in characters:
            yield value[start:index]
            start = index + 1
        elif char == '\\':
            escaped = True

    yield value[start:]


def filter_value_adjust(operator, value):
    if operator not in ("<>*", "<>"):
        return value

    value = value.strip()

    has_wildcard = find_unescaped_characters(value, ["*"])
    if has_wildcard:
        return value

    return "*%s*" % value


def hexdump(content):
    decoded = struct.unpack("B" * len(content), content)
    content = ""
    i = 0

    while i < len(decoded):
        chunk = decoded[i:i+16]
        content += "%.4x:    " % i
        content += " ".join(map(lambda b: "%02x" % b, chunk))

        content += "   " * (16 - len(chunk))
        content += "    "

        for b in chunk:
            if b >= 32 and b < 127:
                content += chr(b)
            else:
                content += "."

        content += "\n"
        i += 16

    return content

def json_type(field):
    """Load a json and correctly encode it."""
    return json_deep_encode(json.loads(field))

def json_deep_encode(obj, encoding="utf-8"):
    """Recursive encode an object."""
    if isinstance(obj, unicode):
        return obj.encode(encoding)

    if isinstance(obj, list):
        return [json_deep_encode(o, encoding) for o in obj]

    if isinstance(obj, dict):
        return dict((json_deep_encode(key, encoding), json_deep_encode(value, encoding)) for key, value in obj.iteritems())

    return obj

class PrewikkaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__json__"):
            return obj.__json__()

        if isinstance(obj, datetime.datetime):
            return str(obj)

        return json.JSONEncoder.default(self, obj)


def deprecated(func):
    """This is a decorator which can be used to mark functions
       as deprecated. It will result in a warning being emitted
       when the function is used."""

    def new_func(*args, **kwargs):
        caller = sys._getframe(1)

        filename = os.path.basename(caller.f_globals["__file__"])
        if filename.endswith((".pyc", ".pyo")):
            filename = filename[:-1]

        env.log.warning("%s:%d call to deprecated function %s." % (filename, caller.f_lineno, func.__name__))
        return func(*args, **kwargs)

    return new_func


class CachingIterator(object):
    def __init__(self, items):
        self._count = None
        self._cache = []
        self._items = iter(items)

    def __len__(self):
        if self._count is None:
            for i in self:
                pass

            self._count = len(self._cache)

        return self._count

    def preprocess_value(self, value):
        return value

    def __iter__(self):
        for i in self._cache:
            yield i

        for i in self._items:
            value = self.preprocess_value(i)
            self._cache.append(value)
            yield value

    def __getitem__(self, key):
        if isinstance(key, slice) :
            return [self[i] for i in xrange(*key.indices(len(self)))]

        elif isinstance(key, int):
            if key < 0:
                key += len(self)

        try:
            for i in xrange((key + 1) - len(self._cache)):
                self._cache.append(self.preprocess_value(next(self._items)))
        except StopIteration:
            raise IndexError

        return self._cache[key]


if sys.hexversion >= 0x02070000:
        from collections import OrderedDict
else:
        from prewikka.compat import OrderedDict
