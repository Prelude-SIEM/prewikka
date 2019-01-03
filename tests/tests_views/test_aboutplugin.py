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
Tests for `prewikka.views.aboutplugin`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest


@pytest.fixture
def aboutplugin_fixtures(request):
    """
    Fixture for aboutplugin tests.

    :return: view for aboutplugin.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.getView(request.param)
    env.request.parameters = view.view_parameters(view)
    env.request.view = view

    return view


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.render_get"], indirect=True)
def test_render_get(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.render_get` view.
    """
    view = aboutplugin_fixtures

    view.render()


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.enable"], indirect=True)
def test_enable(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.enable` view.
    """
    view = aboutplugin_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    env.request.parameters['enable_plugin'] = 'prewikka.views.filter.filter:FilterView'

    view.render()

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.update"], indirect=True)
def test_update(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.update` view.
    """
    view = aboutplugin_fixtures

    view.render()
