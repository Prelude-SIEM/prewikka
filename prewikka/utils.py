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
import re

from prewikka import DataSet
from prewikka.templates import ErrorTemplate

port_dict = {}
read_done = False


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

def escape_attribute(value):   
    # Escape '\' since it's a valid js escape.
    return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("/", "\\/")

def escape_criteria(criteria):
    return criteria.replace("\\", "\\\\").replace("'", "\\'")

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
        link += "&%s" % urllib.urlencode(parameters, doseq=True)

    return link


def property(type, name, parameter, value=None):
    return { "type": type, "name": name, "parameter": parameter, "value": value }


def text_property(name, parameter, value=None):
    return property("text", name, parameter, value)


def password_property(name, parameter):
    return property("password", name, parameter)


def boolean_property(name, parameter, value=False):
    return property("checkbox", name, parameter, value)


def escape_html_string(s):
    s = str(s)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&#39;")
    return s


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
