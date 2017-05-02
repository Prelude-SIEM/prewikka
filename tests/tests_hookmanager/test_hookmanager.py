# Copyright (C) 2018 CS-SI. All Rights Reserved.
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


HOOK_TEST = 'TEST_HOOK'


def fake_function_with_hook():
    """
    Fake function to test hook register. Hook is register only when it's triggered.

    :return: 42
    :rtype: int
    """
    list(hookmanager.trigger(HOOK_TEST, 'foo'))

    return 42


def test_hookmanager_register():
    """
    Test `prewikka.hookmanager.HookManager.register()` method.
    """
    hook_2 = 'hook_2'
    hook_2_method = 'hook_2_method'

    # simple hook
    assert HOOK_TEST not in hookmanager.hookmgr

    hookmanager.register(HOOK_TEST)

    assert HOOK_TEST not in hookmanager.hookmgr

    fake_function_with_hook()

    assert HOOK_TEST in hookmanager.hookmgr

    # hook with _regfunc arg
    assert hook_2 not in hookmanager.hookmgr

    hookmanager.register(hook_2, hook_2_method)

    assert hook_2 in hookmanager.hookmgr


def test_hookmanager_trigger():
    """
    Test `prewikka.hookmanager.HookManager.trigger()` method.
    """
    hook_3 = 'hook_3'
    hook_3_method = 'hook_3_method'

    assert hook_3 not in hookmanager.hookmgr

    hookmanager.register(hook_3, hook_3_method)

    assert hook_3 in hookmanager.hookmgr

    assert list(hookmanager.trigger(hook_3, 'bar'))

    with pytest.raises(Exception):
        list(hookmanager.trigger(hook_3, 'bar', type=str))


def test_hookmanager_unregister():
    """
    Test `prewikka.hookmanager.HookManager.unregister()` method.
    """
    hook_4 = 'hook_4'
    hook_4_method = 'hook_4_method'

    # register
    assert hook_4 not in hookmanager.hookmgr

    hookmanager.register(hook_4, hook_4_method)

    assert hook_4 in hookmanager.hookmgr

    # unregister
    hookmanager.unregister(hook_4, hook_4_method)

    assert hook_4 in hookmanager.hookmgr  # hooks exist but method is empty
