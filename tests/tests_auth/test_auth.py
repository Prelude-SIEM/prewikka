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
Tests for `prewikka.auth.auth`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.auth.auth import Auth, AuthError
from prewikka.config import ConfigSection
from prewikka.error import NotImplementedError
from prewikka.session.session import Session
from prewikka.usergroup import Group, User


def test_autherror():
    """
    Test `prewikka.auth.auth.AuthError` error.
    """
    session = Session(ConfigSection(None))
    error = AuthError(session)

    with pytest.raises(AuthError):
        raise error


def test_auth():
    """
    Test `prewikka.auth.auth.Auth` class.
    """
    auth = Auth(ConfigSection(None))
    user = User('john')
    group = Group('grp')

    # _AuthUser()
    assert not auth.can_create_user()
    assert not auth.can_delete_user()
    assert not auth.can_set_password()
    assert not auth.can_manage_permissions()
    assert not auth.get_user_list()
    assert not auth.get_user_list('foo')

    assert not auth.get_user_by_id(user.id)
    auth.create_user(user)
    assert auth.get_user_by_id(user.id)
    auth.delete_user(user)
    assert not auth.get_user_by_id(user.id)

    with pytest.raises(NotImplementedError):
        auth.has_user(user)

    assert not auth.get_user_permissions(user)
    assert not auth.get_user_permissions(user, True)
    assert not auth.get_user_permissions_from_groups(user)

    with pytest.raises(NotImplementedError):
        auth.set_user_permissions(user, ['FAKE_PERM'])

    # _AuthGroup
    assert not auth.can_create_group()
    assert not auth.can_delete_group()
    assert not auth.can_manage_group_members()
    assert not auth.can_manage_group_permissions()
    assert not auth.get_group_list()
    assert not auth.get_group_list('foo')

    assert not auth.get_group_by_id(group.id)
    auth.create_group(group)
    assert auth.get_group_by_id(group.id)
    auth.delete_group(group)
    assert not auth.get_group_by_id(group.id)

    with pytest.raises(NotImplementedError):
        auth.set_group_permissions(group, ['FAKE_PERM'])

    assert not auth.get_group_permissions(group)

    with pytest.raises(NotImplementedError):
        auth.set_group_members(group, [user])

    assert not auth.get_group_members(group)

    with pytest.raises(NotImplementedError):
        auth.set_member_of(user, [group])

    assert not auth.get_member_of(user)

    with pytest.raises(NotImplementedError):
        auth.is_member_of(group, user)

    with pytest.raises(NotImplementedError):
        auth.has_group(group)
