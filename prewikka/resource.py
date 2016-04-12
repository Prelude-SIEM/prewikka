# -*- coding: utf-8 -*-
# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
#
# Inspired by the tw2.core package of ToscaWidgets2 which is Copyright (c)
# 2006-2013, Paul Johnston, Christopher Perkins, Alberto Valverde González
# and contributors.
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


class Link(object):
    """
    A link to an external resource, like a JS or CSS file.
    """
    def __init__(self, link):
        self.link = link

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        return self.link == getattr(other, "link", None)

    def __str__(self):
        return self.template % self.link


class CSSLink(Link):
    """
    A link to an external CSS file.
    """
    template = """<link rel="stylesheet" type="text/css" href="%s"/>"""


class JSLink(Link):
    """
    A link to an external JS file.
    """
    template = """<script type="text/javascript" src="%s"></script>"""


class Source(object):
    """
    An inlined chunk of source code.
    """
    def __init__(self, src):
        self.src = src

    def __hash__(self):
        return hash(self.src)

    def __eq__(self, other):
        return self.src == getattr(other, "src", None)

    def __str__(self):
        return self.template % self.src


class CSSSource(Source):
    """
    An inlined chunk of CSS source code.
    """
    template = """<style type="text/css">%s</style>"""


class JSSource(Source):
    """
    An inlined chunk of JS source code.
    """
    template = """<script type="text/javascript">%s</script>"""
