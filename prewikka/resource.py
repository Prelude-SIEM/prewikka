# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017 CS-SI. All Rights Reserved.
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


from __future__ import absolute_import, division, print_function, unicode_literals

import functools
from prewikka.utils import html, json


class Link(html.Markup):
    """
    A link to an external resource, like a JS or CSS file.
    """
    pass


class CSSLink(Link):
    """
    A link to an external CSS file.
    """
    def __new__(cls, link):
        return Link.__new__(cls, html.Markup('<link rel="stylesheet" type="text/css" href="%s" />') % link)


class JSLink(Link):
    """
    A link to an external JS file.
    """
    def __new__(cls, link):
        return Link.__new__(cls, html.Markup('<script type="text/javascript" src="%s"></script>') % link)


class HTMLSource(html.Markup):
    pass


class CSSSource(HTMLSource):
    """
    An inlined chunk of CSS source code.
    """
    def __new__(cls, src):
        return HTMLSource.__new__(cls, html.Markup('<style type="text/css">%s</style>') % src)


class JSSource(HTMLSource):
    """
    An inlined chunk of JS source code.
    """
    def __new__(cls, src):
        return HTMLSource.__new__(cls, html.Markup('<script type="text/javascript">%s</script>') % src)


@functools.total_ordering
class HTMLNode(json.JSONObject):
    def __init__(self, tag, *childs, **attrs):
        self.tag = tag
        self.childs = childs

        icon = attrs.pop("_icon", None)
        if icon:
            self.childs = (HTMLNode("i", _class="fa %s" % icon), " ") + self.childs

        self._sortkey = attrs.pop("_sortkey", None)

        tmp = attrs.pop("_class", None)
        if tmp:
            attrs["class"] = tmp

        self.attrs = attrs

    def to_string(self, _class=""):
        attr_s = HTMLSource()
        for k, v in self.attrs.items():
            if k == "class":
                _class += " %s" % v
                continue

            attr_s += HTMLSource(" %s=\"%s\"") % (k, v)

        if _class:
            attr_s = HTMLSource(" class=\"%s\"") % (_class) + attr_s

        childs = HTMLSource()
        for x in self.childs:
            childs += text_type(x)

        return HTMLSource("<%s%s>%s</%s>" % (self.tag, attr_s, childs, self.tag))

    def __json__(self):
        return {"tag": self.tag, "childs": self.childs, "attrs": self.attrs}

    def __str__(self):
        return self.to_string()

    def __eq__(self, other):
        return (self._sortkey, self.childs) == (other._sortkey, other.childs)

    def __lt__(self, other):
        return (self._sortkey, self.childs) < (other._sortkey, other.childs)
