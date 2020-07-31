# Copyright (C) 2014-2020 CS GROUP - France. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

import glob
import os

import pkg_resources


def get_themes():
    theme_list = []

    css_files = glob.glob(pkg_resources.resource_filename(__name__, "htdocs/css/themes/*.css"))
    for css in css_files:
        theme_list.append(os.path.basename(css)[:-4])

    theme_list.sort()
    return theme_list
