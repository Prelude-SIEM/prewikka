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


from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.utils import html


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
