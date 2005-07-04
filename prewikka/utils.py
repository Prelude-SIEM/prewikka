# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


import time, calendar
import struct
import urllib

from prewikka import DataSet
from prewikka.templates import ErrorTemplate


def escape_attribute(value):
    return value.replace("'", "\\'")

def escape_criteria(criteria):
    return criteria.replace("'", "\\'")

def time_to_hms(t):
    return time.strftime("%H:%M:%S", t)


def time_to_ymdhms(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", t)


def get_gmt_offset():
    utc = int(time.time())
    tm = time.localtime(utc)
    local = calendar.timegm(tm)

    offset = local - utc

    return (offset / 3600, offset % 3600 / 60)


def urlencode(parameters, doseq=False):
    return urllib.urlencode(parameters, doseq).replace('&', '&amp;')


def create_link(action_name, parameters=None):
    link = "?view=%s" % action_name
    if parameters:
        link += "&amp;%s" % urllib.urlencode(parameters, doseq=True).replace('&', '&amp;')

    return link


def property(type, name, parameter, value=None):
    return { "type": type, "name": name, "parameter": parameter, "value": value }


def text_property(name, parameter, value=None):
    return property("text", name, parameter, value)


def password_property(name, parameter):
    return property("password", name, parameter)


def boolean_property(name, parameter, value=False):
    return property("checkbox", name, parameter, value)


def escape_html_char(c):
    try:
        return {
            ">": "&gt;",
            "<": "&lt;",
            "&": "&amp;",
            "\"": "&quot;",
            "'": "&#39;"
            }[c]
    except KeyError:
        return c


def escape_html_string(s):
    return "".join(map(lambda c: escape_html_char(c), str(s)))


def hexdump(content):
    decoded = struct.unpack("B" * len(content), content)
    content = ""
    i = 0

    while i < len(decoded):
        chunk = decoded[i:i+16]
        
        content += " ".join(map(lambda b: "%02x" % b, chunk)) + " "
        
        for b in chunk:
            if b >= 32 and b < 127:
                content += escape_html_char(chr(b))
            else:
                content += "."

        content += "<br/>"

        i += 16

    return "<div class='fixed'>" + content + "</div>"
