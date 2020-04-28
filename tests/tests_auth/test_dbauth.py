# Copyright (C) 2020 CS-SI. All Rights Reserved.
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
Tests for `prewikka.auth.dbauth`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.auth.dbauth import DBAuth
from prewikka.config import ConfigSection
from prewikka.usergroup import Group, User


def test_dbauth():
    """
    Test `prewikka.auth.dbauth.DBAuth` class.
    """
    auth = DBAuth(ConfigSection(None))
    user = User('john')
    group = Group('grp')

    assert auth.can_create_user()
    assert auth.can_delete_user()
    assert auth.can_set_password()
    assert auth.can_manage_permissions()

    assert not auth.get_user_by_id(user.id)
    auth.create_user(user)
    assert auth.has_user(user)
    assert auth.get_user_by_id(user.id)
    assert user in auth.get_user_list()
    assert user in auth.get_user_list('jo')

    auth.set_user_permissions(user, ['FAKE_PERM1'])
    assert 'FAKE_PERM1' in auth.get_user_permissions(user)
    assert 'FAKE_PERM1' in auth.get_user_permissions(user, True)

    assert auth.can_create_group()
    assert auth.can_delete_group()
    assert auth.can_manage_group_members()
    assert auth.can_manage_group_permissions()

    assert not auth.get_group_by_id(group.id)
    auth.create_group(group)
    assert auth.has_group(group)
    assert auth.get_group_by_id(group.id)
    assert group in auth.get_group_list()
    assert group in auth.get_group_list('gr')

    auth.set_group_members(group, [user])
    assert user in auth.get_group_members(group)

    auth.set_member_of(user, [group])
    assert group in auth.get_member_of(user)

    assert auth.is_member_of(group, user)

    auth.set_group_permissions(group, ['FAKE_PERM2'])
    assert 'FAKE_PERM2' in auth.get_group_permissions(group)
    assert 'FAKE_PERM2' in auth.get_user_permissions(user)
    assert 'FAKE_PERM2' not in auth.get_user_permissions(user, True)
    assert 'FAKE_PERM2' in auth.get_user_permissions_from_groups(user)

    auth.delete_user(user)
    assert not auth.get_user_by_id(user.id)

    auth.delete_group(group)
    assert not auth.get_group_by_id(group.id)
