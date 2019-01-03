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
Utils for `prewikka.session` tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import binascii
import os
import struct
import time

from prewikka.session.anonymous.anonymous import AnonymousSession
from prewikka.session.session import SessionDatabase


class FakeAuthBackend(AnonymousSession):
    """
    Fake Auth backend for test suite.
    """
    def has_user(self, other):
        return False

    def get_user_permissions_from_groups(self, user):
        pass

    def set_user_permissions(self, user, permissions):
        pass

    def get_default_session(self):
        pass

    def get_group_by_id(self, id_):
        pass

    def has_group(self, group):
        pass

    def is_member_of(self, group, user):
        pass

    def set_group_members(self, group, users):
        pass

    def set_group_permissions(self, group, permissions):
        pass

    def set_member_of(self, user, groups):
        pass


def create_session(user, time_=None, session_id=None):
    """
    Create a session and save it in database.

    :param rewikka.usergroup.User user: User for the session creation.
    :param float time_: optional time.time() object.
    :param str session_id: optional session ID
    :return: the ID of the session.
    :rtype: str
    """
    if not time_:
        time_ = time.time()

    if not session_id:
        session_id = binascii.hexlify(os.urandom(16) + struct.pack(b'>d', time_))

    session_database = SessionDatabase()
    session_database.create_session(session_id, user, int(time_))

    return session_id


def clean_sessions():
    """
    Delete all sessions in `prewikka_session` table.

    :return: None
    :rtype: None
    """
    env.db.query('DELETE FROM Prewikka_Session;')
