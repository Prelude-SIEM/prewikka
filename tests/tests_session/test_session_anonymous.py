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
Tests for `prewikka.session.anonymous.anonymous`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.config import ConfigSection
from prewikka.session.anonymous.anonymous import AnonymousSession


def test_anonymous_session():
    """
    Test `prewikka.session.anonymous.anonymous.AnonymousSession` class.

    Anonymous do not really implements all methods of Session class, just checks all works by default.
    """
    anonymous_session = AnonymousSession(ConfigSection(""))

    assert anonymous_session.get_user_permissions(None)
    assert anonymous_session.get_user_info(None)
    assert anonymous_session.get_user_list()
    assert anonymous_session.get_user_by_id(None)
    assert anonymous_session.has_user(None)
    assert anonymous_session.authenticate(None, None)
