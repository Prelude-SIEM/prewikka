# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
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

import markupsafe


class Markup(markupsafe.Markup):
    @classmethod
    def escape(cls, value):
        if value is None:
            return Markup()

        return markupsafe.escape(value)


def escape(value):
    return Markup.escape(value)

def escapejson(value):
    return value.replace("</", "<\\/")


def selected(condition):
    return "selected" if condition else ""

def checked(condition):
    return "checked" if condition else ""

def disabled(condition):
    return "disabled" if condition else ""
