# Copyright (C) 2014-2020 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
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

from prewikka import resource


def compute_charts_infos(chart_infos, tooltips=None):
    cinfos = []

    for title, categories, charts in chart_infos:
        s = sc = resource.HTMLSource("%s") % _(title)
        if categories:
            sub_info = resource.HTMLSource(", ").join(resource.HTMLNode("abbr", _(c), title=_(tooltips[c]), **{'data-toggle': 'tooltip'}) for c in categories)
            sub_info_c = resource.HTMLSource(", ").join(resource.HTMLSource("%s") % _(c) for c in categories)
            s += resource.HTMLSource(" (%s)") % sub_info
            sc += resource.HTMLSource(" (%s)") % sub_info_c

        cinfos += [{'title': s, 'title_c': sc, 'category': 'text', 'width': 12, 'height': 1}] + charts

    return cinfos
