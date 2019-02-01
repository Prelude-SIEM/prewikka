# Copyright (C) 2004-2018 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import os.path
import re
import struct
import sys
import time
import unicodedata

from prewikka import compat


port_dict = {}
read_done = False

if sys.version_info >= (3, 0):
    text_type = str
else:
    text_type = unicode


class AttrObj(object):
    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    def __json__(self):
        return self.__dict__

    def __repr__(self):
        return self.__dict__.__repr__()

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __iter__(self):
        if sys.version_info >= (3, 0):
            return self.__dict__.items()
        else:
            return self.__dict__.iteritems()


# FIXME: Need appropriate implementation
def get_analyzer_status_from_latest_heartbeat(heartbeat, error_margin):
    res = heartbeat.get("additional_data('Analyzer status').data")
    if res and res[0] == "exiting":
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
    sreg = re.compile("^\s*(?P<name>[^#]\S+)\s*(?P<number>\d+)\s*(?P<alias>\S+)")

    try:
        fd = open("/etc/protocols", "r")
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

    if num in port_dict:
        return port_dict[num][0]

    return None


def nameToPath(name):
    if not isinstance(name, compat.STRING_TYPES):
        name = text_type(name)

    return name.lower().replace(" ", "_")


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


# Based on Python recipes 52213
def soundex(name):
    """ soundex module conforming to Knuth's algorithm
        implementation 2000-12-24 by Gregory Jorgensen
        public domain
    """

    # digits holds the soundex values for the alphabet
    digits = '01230120022455012623010202'
    sndx = ''
    fc = ''

    # We need to call text_type() so that we work on a string (not bytes) with Py3
    name = text_type(unicodedata.normalize("NFKD", name).encode("ascii", "ignore"))

    # translate alpha chars in name to soundex digits
    for i, c in enumerate(name):
        if c.isalpha():
            if not fc:
                fc = c   # remember first letter

            idx = ord(c.upper()) - ord('A')
            if idx >= len(digits):
                continue

            d = digits[idx]
            # duplicate consecutive soundex digits are skipped
            if not sndx or (d != sndx[-1]) or (len(sndx) > 1 and d == sndx[-2] and name[i - 1].upper() not in ['W', 'H']):
                sndx += d

    # replace first digit with first alpha character
    # remove all 0s from the soundex code
    return (fc.upper() + sndx[1:]).replace('0', '')


def hexdump(content):
    decoded = struct.unpack(b"B" * len(content), content)
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


def path_sort_key(path):
    """
    Return a key to sort dataprovider paths in natural order,
    so that alert.source(10) comes after alert.source(2).
    """
    return [int(part) if part.isdigit() else part for part in re.split("(\d+)", path)]


class CachingIterator(object):
    def __init__(self, items, count=None):
        self._count = count
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

        # Some iterables can be read through multiple times. We disable this here
        # This will avoid duplicate data in self._cache
        self._items = iter([])

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]

        elif isinstance(key, int):
            if key < 0:
                key += len(self)

        try:
            for i in range((key + 1) - len(self._cache)):
                self._cache.append(self.preprocess_value(next(self._items)))
        except StopIteration:
            raise IndexError

        return self._cache[key]

    def __json__(self):
        return list(self)
