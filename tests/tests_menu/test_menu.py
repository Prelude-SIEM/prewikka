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
Tests for `prewikka.menu`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from prewikka.error import PrewikkaUserError
from prewikka.menu import MenuManager
from tests.utils.vars import TEST_DATA_DIR


def test_menu_manager():
    """
    Test `prewikka.menu.MenuManager` class.
    """
    backup_interface = env.config.interface

    # default
    MenuManager()

    # invalid menu (empty)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_empty.yml')}
        MenuManager()

    # invalid menu (no name AND no icon)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_no_name_and_no_icon.yml')}
        MenuManager()

    # invalid menu (multiple default menu)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_multiple_default.yml')}
        MenuManager()

    # valid menu (no default)
    env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_no_default.yml')}
    MenuManager()

    # invalid menu (section without name)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_section_no_name.yml')}
        MenuManager()

    # invalid menu (section with multiple default tab)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {
            'menu_order': os.path.join(TEST_DATA_DIR, 'menu_section_multiple_default_tab.yml')
        }
        MenuManager()

    # clean
    env.config.interface = backup_interface


def test_menu_manager_methods():
    """
    Test `prewikka.menu.MenuManager` methods.
    """
    menu_manager = MenuManager()

    assert menu_manager.get_sections() == {}
    assert menu_manager.get_menus()
    assert menu_manager.get_declared_sections()

    menu_manager.add_section_info('section', 'tab', 'endpoint')
