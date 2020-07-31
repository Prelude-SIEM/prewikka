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
Tests for `prewikka.usergroup`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.error import NotImplementedError
from prewikka.usergroup import PermissionDeniedError, Group, User, permissions_required


@permissions_required(['perm1', 'perm2'])
def fake_function():
    """
    Fake function for tests.
    :return: 42
    """
    return 42


def test_permission_denied_error():
    """
    Test `prewikka.usergroup.PermissionDeniedError` error.
    """
    assert PermissionDeniedError('access_file', 'foo')
    assert PermissionDeniedError(None, 'foo')
    assert PermissionDeniedError('access_file')


def test_group():
    """
    Test `prewikka.usergroup.Group` class.
    """
    with pytest.raises(Exception):
        Group()

    group1 = Group(name='foo')
    group2 = Group(name='bar')

    group1.create()
    assert group1 != group2
    assert group1.name == 'foo'
    assert group1 == Group(groupid=group1.id)

    group1.delete()


def test_permissions_required():
    """
    Test `prewikka.usergroup.permissions_required` decorator.
    """
    # env.request.user != None
    fake_function()

    # env.request.user == None
    backup_user = env.request.user
    env.request.user = None

    fake_function()

    env.request.user = backup_user


def test_user():
    """
    Test `prewikka.usergroup.User` class.
    """
    with pytest.raises(Exception):
        User()

    user1 = User(login='foo')
    user2 = User(login='bar')

    user1.create()
    assert user1 != user2
    assert user1.name == 'foo'
    assert user1 == User(userid=user1.id)

    # set permissions (not implemented)
    with pytest.raises(NotImplementedError):
        user1.permissions = 'perm1'

    user1._permissions = 'perm2'

    # set_locale()
    user1.set_locale()

    backup_locale = env.config.general.default_locale
    env.config.general.default_locale = None
    user1.set_locale()
    env.config.general.default_locale = backup_locale

    # set_property()
    user1.set_property('key1', '1')
    user1.set_property('key2', '2', '/agents/agents')

    # get_property()
    assert user1.get_property('key1') == '1'
    assert user1.get_property('key2', '/agents/agents') == '2'
    assert user1.get_property('key3', '/agents/agents', '3') == '3'

    # del_property()
    user1.del_property(None)
    user1.del_property('key1')

    assert not user1.get_property('key1')

    user1.del_property(None, '/agents/agents')
    user1.del_property('key2', '/agents/agents')

    assert not user1.get_property('key2')

    # del_properties()
    user1.set_property('key4', '4', '/agents/agents')

    assert user1.get_property('key4', '/agents/agents') == '4'

    user1.set_property('key5', '5', '/agents/agents')

    assert user1.get_property('key5', '/agents/agents') == '5'

    user1.del_properties('/agents/agents')

    assert not user1.get_property('key4', '/agents/agents')
    assert not user1.get_property('key5', '/agents/agents')

    # del_property_match()
    user1.set_property('key6', '6')

    assert user1.get_property('key6') == '6'

    user1.del_property_match('key6')

    user1.set_property('key7', '7', '/agents/agents')

    assert user1.get_property('key7', '/agents/agents') == '7'

    user1.del_property_match('key7', '/agents/agents')

    user1.set_property('key8', '8', '/agents/agents')
    user1.del_property_match('key999', '/agents/agents')

    user1.del_property_match('key9', '/agents/list')

    # get_property_fail()
    with pytest.raises(KeyError):
        user1.get_property_fail('key10', '10')

    user1.set_property('key11', '11')

    # sync_properties()
    user1.sync_properties()

    # has()
    assert not user1.has(['foo'])
    assert not user1.has(('foo',))
    assert not user1.has(set('foo'))
    assert not user1.has('foo')

    # check()
    with pytest.raises(PermissionDeniedError):
        user1.check('perm1')

    with pytest.raises(PermissionDeniedError):
        user1.check('perm1', '/agents/agents')

    user1.delete()
