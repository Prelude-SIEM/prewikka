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
Test for `prewikka.hookmanager`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka import hookmanager


def test_hookmanager_register():
    """
    Test `prewikka.hookmanager.HookManager.register()` method.
    """
    hook = 'hook_1'

    assert hook not in hookmanager.hookmgr

    hookmanager.register(hook, lambda x: 42)

    assert hook in hookmanager.hookmgr


def test_hookmanager_trigger():
    """
    Test `prewikka.hookmanager.HookManager.trigger()` method.
    """
    # Test method return value
    hook = 'hook_2'
    hookmanager.register(hook, lambda x: x + '42')

    assert list(hookmanager.trigger(hook, 'bar')) == ['bar42']

    with pytest.raises(TypeError):
        list(hookmanager.trigger(hook, 'foo', 'bar'))

    with pytest.raises(TypeError):
        list(hookmanager.trigger(hook, 'bar', type=int))

    # Test exception handling
    hook = 'hook_3'
    hookmanager.register(hook, lambda x: 1/x)

    with pytest.raises(ZeroDivisionError):
        list(hookmanager.trigger(hook, 0))

    assert list(hookmanager.trigger(hook, 0, _except=lambda e: None)) == []

    # Test constant value
    hook = 'hook_4'
    hookmanager.register(hook, 42)

    assert list(hookmanager.trigger(hook, type=int)) == [42]

    # Test return ordering
    hook = 'hook_5'
    hookmanager.register(hook, 'a', _order=2)
    hookmanager.register(hook, 'b', _order=1)
    hookmanager.register(hook, 'r', _order=3)

    assert ''.join(hookmanager.trigger(hook)) == 'bar'


def test_hookmanager_unregister():
    """
    Test `prewikka.hookmanager.HookManager.unregister()` method.
    """
    hook = 'hook_6'
    method = lambda x: x

    hookmanager.register(hook, method)
    hookmanager.unregister(hook, method)

    assert list(hookmanager.trigger(hook, 'bar')) == []
