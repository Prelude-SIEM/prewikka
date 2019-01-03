# Copyright (C) 2018-2019 CS-SI. All Rights Reserved.
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
Tests for `prewikka.renderer`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.renderer import COLOR_MAP, RED_STD, GRAY_STD, SEVERITY_COLOR_MAP, \
    RendererNoDataException, RendererItem, RendererUtils, RendererPluginManager


def test_renderer_no_data_exception():
    """
    Test `prewikka.renderer.RendererNoDataException` exception.
    """
    exc = RendererNoDataException()

    with pytest.raises(RendererNoDataException):
        raise exc

    assert text_type(exc)


def test_renderer_item():
    """
    Test `prewikka.renderer.RendererItem` class.
    """
    renderer_item = RendererItem()

    assert not renderer_item[0]
    assert not renderer_item[1]
    assert not renderer_item[2]


def test_renderer_utils():
    """
    Test `prewikka.renderer.RendererUtils` class.
    """
    renderer_utils = RendererUtils({})

    assert renderer_utils.get_label('foo') == 'foo'
    assert renderer_utils.get_color('foo') == COLOR_MAP[0]
    assert renderer_utils.get_color('bar') == COLOR_MAP[1]

    renderer_utils = RendererUtils({'names_and_colors': SEVERITY_COLOR_MAP})

    assert renderer_utils.get_label('high') == 'High'
    assert renderer_utils.get_label('invalid') == 'n/a'
    assert renderer_utils.get_color('high') == RED_STD
    assert renderer_utils.get_color('invalid') == GRAY_STD


def test_renderer_plugin_manager():
    """
    Test `prewikka.renderer.RendererPluginManager` class.
    """
    all_plugins = env.all_plugins
    env.all_plugins = {}

    renderer = RendererPluginManager()

    assert set(renderer.get_types()) == set(["bar", "timebar"])
    assert renderer.has_backend("chartjs")
    assert renderer.get_backends("bar")
    assert renderer.get_backends_instances("bar")
    assert renderer.get_default_backend("bar") == "chartjs"

    assert renderer.render("bar", [[(34, "foo", None), (11, "bar", None)]])["script"] is not None

    env.all_plugins = all_plugins
