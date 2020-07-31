# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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

"""
Tests for `prewikka.pluginmanager`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.pluginmanager import PluginBase, PluginPreload


def test_plugin_base():
    """
    Test `prewikka.pluginmanager.PluginBase` class.
    """
    PluginBase()


def test_plugin_preload():
    """
    Test `prewikka.pluginmanager.PluginPreload` class.
    """
    PluginPreload()
