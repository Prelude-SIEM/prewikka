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
Tests for `prewikka.auth`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.auth.auth import AuthError, Auth
from prewikka.error import NotImplementedError
from prewikka.usergroup import User


class FakeSession(object):
    """
    Fake class to emulate Session system, tests only.
    """
    template = None

    def __init__(self, template):
        self.template = template


class FakeAuth(Auth):
    """
    Fake class to emulate Auth system, tests only.
    """
    pass


def test_autherror():
    """
    Test `prewikka.auth.auth.AuthError` error.
    """
    session = FakeSession(None)
    error = AuthError(session)

    with pytest.raises(AuthError):
        raise error


def test_auth():
    """
    Test `prewikka.auth.auth.Auth` class.
    """
    authentication = FakeAuth(None)

    # _AuthUser()
    assert not authentication.can_create_user()
    assert not authentication.can_delete_user()
    assert not authentication.can_set_password()
    assert not authentication.can_manage_permissions()

    with pytest.raises(NotImplementedError):
        assert not authentication.create_user('john')

    with pytest.raises(NotImplementedError):
        assert not authentication.delete_user(User('john'))

    assert not authentication.get_user_list()
    assert not authentication.get_user_list('foo')

    with pytest.raises(NotImplementedError):
        authentication.get_user_by_id('john')

    with pytest.raises(NotImplementedError):
        authentication.has_user('john')

    assert not authentication.get_user_permissions('john')
    assert not authentication.get_user_permissions('john', True)
    assert not authentication.get_user_permissions_from_groups('bar')

    with pytest.raises(NotImplementedError):
        authentication.set_user_permissions('john', 'fake-perms')

    # _AuthGroup
    assert not authentication.can_create_group()
    assert not authentication.can_delete_group()
    assert not authentication.can_manage_group_members()
    assert not authentication.can_manage_group_permissions()
    assert not authentication.get_group_list()
    assert not authentication.get_group_list('foo')

    with pytest.raises(NotImplementedError):
        authentication.get_group_by_id('grp')

    with pytest.raises(NotImplementedError):
        assert not authentication.create_group('grp')

    with pytest.raises(NotImplementedError):
        assert not authentication.delete_group('grp')

    with pytest.raises(NotImplementedError):
        authentication.set_group_permissions('grp', 'perms')

    assert not authentication.get_group_permissions('grp')

    with pytest.raises(NotImplementedError):
        authentication.set_group_members('grp', 'john')

    assert not authentication.get_group_members('grp')

    with pytest.raises(NotImplementedError):
        authentication.set_member_of('john', 'grp')

    assert not authentication.get_member_of('john, ')

    with pytest.raises(NotImplementedError):
        authentication.is_member_of('grp', 'john')

    with pytest.raises(NotImplementedError):
        authentication.has_group('grp')
