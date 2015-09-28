# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
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

import time, sys, re, struct, urllib

port_dict = {}
read_done = False

# FIXME: Need appropriate implementation
def get_analyzer_status_from_latest_heartbeat(heartbeat, error_margin):
    if heartbeat.get("additional_data('Analyzer status')") == "exiting":
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
    return name.lower().replace(" ", "_")

def escape_attribute(value):
    # Escape '\' since it's a valid js escape.
    return value.replace("\\", "\\\\").replace("\"", "\\\"").replace("/", "\\/")

def escape_criteria(criteria):
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
    if not isinstance(s, (str, unicode)):
        s = str(s)

    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&#39;")
    return s


def _criteria_value_find(value, clist=[]):
    escaped = False

    for char in value:
        if escaped:
            escaped = False
        elif char in clist:
            return True
        elif char == '\\':
            escaped = True

    return False


def filter_value_adjust(operator, value):
    if operator not in ("<>*", "<>"):
        return value

    value = value.strip()

    has_wildcard = _criteria_value_find(value, ["*"])
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


if sys.hexversion >= 0x02070000:
        from collections import OrderedDict
else:
        from prewikka.compat import OrderedDict
