# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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


import time

from prewikka import DataSet
from prewikka.templates import ErrorTemplate

def time_to_hms(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


def time_to_ymdhms(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))


def create_link(action_name, parameters=None):
    link = "?action=%s" % action_name
    if parameters:
        link += "&%s" % str(parameters)
        
    return link


def property(type, name, parameter, value=None):
    return { "type": type, "name": name, "parameter": parameter, "value": value }


def text_property(name, parameter, value=None):
    return property("text", name, parameter, value)


def password_property(name, parameter):
    return property("password", name, parameter)


def boolean_property(name, parameter, value=False):
    return property("checkbox", name, parameter, value)


def mixin(*bases):
    class Dummy:
        def __init__(self):
            for base in Dummy.__bases__:
                if hasattr(base, "__init__"):
                    base.__init__(self)

    Dummy.__bases__ = bases
    
    return Dummy()
