# Copyright (C) 2018-2020 CS-SI. All Rights Reserved.
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
Pytest fixtures.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import copy

import pytest

from prewikka import config, main, usergroup
from prewikka.web.request import cookies
from tests.utils.database import init_idmef_database, clean_database
from tests.utils.fixtures import FakeInitialRequest, clean_directory
from tests.utils.vars import TEST_CONFIG_FILE, TEST_DOWNLOAD_DIR, TEST_SESSION_ID


@pytest.fixture(scope='session', autouse=True)
def initialization_fixtures(request):
    """
    Main fixture for all tests: load Prewikka out of browser by setup
    configuration.

    Configuration and databases information are loaded through default testing file
    or specific configuration file.

    @pytest.fixture:
        scope=session   caching lifecycle of fixture, available during all tests of
                        the run
        autouse=True    activated for all tests that can see it
    """
    # init IDMEF database
    init_idmef_database(config.Config(TEST_CONFIG_FILE))

    # init prewikka core with config file
    core = main.Core.from_config(TEST_CONFIG_FILE, autoupdate=True)

    # setup "env.request"
    initial_request = FakeInitialRequest('/')

    # load prewikka to setup all settings
    core.process(initial_request)

    # setup "env.request.web.input_cookie"
    cookie = cookies.SimpleCookie()
    cookie[str('sessionid')] = TEST_SESSION_ID  # force str() type to avoid TypeError, works with both py2 and py3
    env.request.web.input_cookie = dict(cookie.items())

    # setup "env.request.dataset" and "env.request.parameters"
    # used only when just a specific test is launched to prevent fails
    env.request.dataset = {}
    env.request.menu_parameters = {
        'timeline_value': 0,
        'timeline_unit': 'day',
        'timeline_absolute': None,
        'auto_apply_value': None
    }

    # setup "env.request.user"
    env.request.user = usergroup.User('anonymous')

    def tear_down():
        """
        TearDown

        - clean IDMEF database
        - clean Prewikka database
        - clean "downloads" directory
        """
        clean_database(env.config.idmef_database)
        clean_database(env.config.database)
        clean_directory(TEST_DOWNLOAD_DIR)

    request.addfinalizer(tear_down)


@pytest.fixture(scope='function', autouse=True)
def prewikka_fixtures(request):
    """
    Fixture used on each test (automatically used).
    """
    backup_request = copy.copy(env.request)

    def tear_down():
        """
        TearDown

        - clean IDMEF tables (TODO)
        - clean env.request
        """
        env.request = backup_request

    request.addfinalizer(tear_down)
