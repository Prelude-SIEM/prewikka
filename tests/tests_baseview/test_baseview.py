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
Tests for `prewikka.baseview`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import copy

import pytest

from prewikka import hookmanager
from prewikka.error import PrewikkaUserError
from prewikka.utils import AttrObj, mkdownload
from tests.utils.fixtures import load_view_for_fixtures


@pytest.fixture()
def baseview_fixtures(request):
    """
    Fixtures for tests of `prewikka.baseview`.
    """
    # view
    load_view_for_fixtures('BaseView.render')

    # dataset
    backup_dataset = copy(env.request.dataset)
    dataset = {'document': AttrObj()}
    env.request.dataset = dataset

    def tear_down():
        """
        TearDown
        """
        env.request.dataset = backup_dataset

    request.addfinalizer(tear_down)


def test_baseview_download(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.download` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    # invalid user
    with pytest.raises(PrewikkaUserError):
        base_view.download('invalid_user', 42, 'test.txt')

    # valid user
    filename = 'test.txt'
    file_created = mkdownload(filename, user=env.request.user.name)
    base_view.download(env.request.user.name, file_created._id, file_created._dlname)

    # no user
    with pytest.raises(PrewikkaUserError):
        filename = 'test2.txt'
        file_created = mkdownload(filename)
        base_view.download(True, file_created._id, file_created._dlname)


def test_baseview_logout(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.logout` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    assert base_view.logout().code == 302


def test_baseview_render(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.render` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    # register a fake HOOK to test all lines in baseview
    hookmanager.register('HOOK_LOAD_HEAD_CONTENT', '<script src="foo.js"></script>')
    hookmanager.register('HOOK_LOAD_BODY_CONTENT', '<foo>bar</foo>')

    # default render
    base_view.render()

    # no user
    backup_user = env.request.user
    env.request.user = None
    base_view.render()
    env.request.user = backup_user

    # clean
    hookmanager.unregister('HOOK_LOAD_HEAD_CONTENT', '<script src="foo.js"></script>')
    hookmanager.unregister('HOOK_LOAD_BODY_CONTENT', '<foo>bar</foo>')
