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
Tests for `prewikka.session.session`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy
import datetime
import sys
import time

if sys.version_info >= (3, 0):
    from http import cookies
else:
    import Cookie as cookies

import pytest

from prewikka.config import ConfigSection
from prewikka.session.session import SessionInvalid, SessionExpired, SessionDatabase, Session
from prewikka.usergroup import User
from tests.fixtures import TEST_SESSION_ID
from tests.tests_session.utils import FakeAuthBackend, create_session, clean_sessions


def test_session_invalid():
    """
    Test `prewikka.session.session.SessionInvalid` error.
    """
    session_invalid = SessionInvalid()

    with pytest.raises(SessionInvalid):
        raise session_invalid

    session_invalid = SessionInvalid(login='test')

    with pytest.raises(SessionInvalid):
        raise session_invalid


def test_session_expired():
    """
    Test `prewikka.session.session.SessionExpired` error.
    """
    session_expired = SessionExpired()

    with pytest.raises(SessionExpired):
        raise session_expired

    session_expired = SessionExpired(login='test')

    with pytest.raises(SessionExpired):
        raise session_expired


def test_session_db_create_():
    """
    Test `prewikka.session.session.SessionDatabase.create_session` method.
    """
    user = User('admin')
    session_id = create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 1
    assert session_id in query.toString()
    assert user.name in query.toString()

    clean_sessions()


def test_session_db_update():
    """
    Test `prewikka.session.session.SessionDatabase.update_session` method.
    """
    session_database = SessionDatabase()
    user = User('admin')
    session_id = create_session(user)
    old_query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)
    time_ = time.time() + 3600  # add 3600s
    session_database.update_session(session_id, time_)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert old_query.toString() != query.toString()
    assert query.getRowCount() == 1
    assert session_id in query.toString()
    assert user.name in query.toString()
    assert datetime.datetime.utcfromtimestamp(time_).strftime('%Y-%m-%d %H:%M:%S')in query.toString()

    # wrong session_id: nothing happening
    fake_session_id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    session_database.update_session(fake_session_id, time_)

    clean_sessions()


def test_session_db_get():
    """
    Test `prewikka.session.session.SessionDatabase.get_session` method.
    """
    session_database = SessionDatabase()
    user = User('admin')
    session_id = create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 1

    username, time_ = session_database.get_session(session_id)

    assert username == user.name
    assert datetime.datetime.utcfromtimestamp(time_).strftime('%Y-%m-%d %H:%M:%S')in query.toString()

    # wrong session_id: fail
    with pytest.raises(Exception):
        fake_session_id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        session_database.get_session(fake_session_id)

    clean_sessions()


def test_session_db_delete():
    """
    Test `prewikka.session.session.SessionDatabase.delete_session` method.
    """
    session_database = SessionDatabase()
    user = User('admin')

    # delete 1 session based on sessionid
    session_id = create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 1

    session_database.delete_session(sessionid=session_id)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 0

    # delete 1 session based on userid
    session_id = create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert session_id in query.toString()
    assert query.getRowCount() == 1

    session_database.delete_session(user=user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 0

    # delete multiple sessions based on userid
    session_id_1 = create_session(user)
    session_id_2 = create_session(user)
    session_id_3 = create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert session_id_1 in query.toString()
    assert session_id_2 in query.toString()
    assert session_id_3 in query.toString()
    assert query.getRowCount() == 3

    session_database.delete_session(user=user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 0

    clean_sessions()

    # delete session based on invalid sessionid: nothing happening
    create_session(user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 1

    fake_session_id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    session_database.delete_session(sessionid=fake_session_id)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 1

    # delete session based on invalid userid: nothing happening
    fake_user = User('fake')
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % fake_user.id)

    assert query.getRowCount() == 0

    session_database.delete_session(user=fake_user)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 1

    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % fake_user.id)

    assert query.getRowCount() == 0

    # delete session with both userid and sessionid: fail
    with pytest.raises(Exception):
        fake_session_id = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        fake_user_id = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'
        session_database.delete_session(sessionid=fake_session_id, user=fake_user_id)

    # delete session without userid and sessionid: nothing
    session_database.delete_session(sessionid=None, user=None)

    clean_sessions()


def test_session_db_delete_expired_():
    """
    Test `prewikka.session.session.SessionDatabase.delete_expired_sessions` method.
    """
    session_database = SessionDatabase()
    user = User('admin')
    t_now = time.time()
    t_before = t_now - 3600
    t_after = t_now + 3600

    # without sessions in database
    session_database.delete_expired_sessions(t_now)

    # with 1 session expired in database
    session_id = create_session(user, t_before)
    session_database.delete_expired_sessions(t_now)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 0

    # with 1 session NOT expired in database
    session_id = create_session(user, t_after)
    session_database.delete_expired_sessions(t_now)
    query = env.db.query('SELECT * from Prewikka_Session WHERE sessionid=\'%s\'' % session_id)

    assert query.getRowCount() == 1

    clean_sessions()

    # with 2 sessions expired and 1 not expired
    session_id_1 = create_session(user, t_before)
    session_id_2 = create_session(user, t_before)
    session_id_3 = create_session(user, t_after)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 3

    session_database.delete_expired_sessions(t_now)
    query = env.db.query('SELECT * from Prewikka_Session WHERE userid=\'%s\'' % user.id)

    assert query.getRowCount() == 1
    assert session_id_1 not in query.toString()
    assert session_id_2 not in query.toString()
    assert session_id_3 in query.toString()

    clean_sessions()


def test_session():
    """
    Test `prewikka.session.session.Session` class.
    """
    session_config = ConfigSection("")
    session_config.expiration = 60  # 1 hour
    create_session(env.request.user, session_id=TEST_SESSION_ID)
    req = deepcopy(env.request.web)

    # __init__()
    session = Session(session_config)

    # get_user()
    user_from_session = session.get_user(req)

    assert env.request.user == user_from_session

    # get_user() with old (but valid) cookie
    clean_sessions()
    create_session(env.request.user, time_=time.time()-3600, session_id=TEST_SESSION_ID)
    user_from_session = session.get_user(req)

    assert env.request.user == user_from_session

    # get_user() with invalid session (empty cookie)
    with pytest.raises(SessionInvalid):
        req = deepcopy(env.request.web)
        req.input_cookie = {}
        session.get_user(req)

    # get_user() with expired session (AJAX request)
    with pytest.raises(SessionExpired):
        req = deepcopy(env.request.web)
        req.input_cookie = {}
        req.is_xhr = True
        session.get_user(req)

    # get_user() with invalid session (bad session_id)
    with pytest.raises(SessionInvalid):
        req = deepcopy(env.request.web)
        req.input_cookie['sessionid'] = cookies.Morsel()
        req.input_cookie['sessionid'].value = 'invalid'
        session.get_user(req)

    # get_user() with expired session (cookie expired)
    with pytest.raises(SessionExpired):
        clean_sessions()
        req = deepcopy(env.request.web)
        create_session(env.request.user, time_=time.time()-3600*24, session_id=TEST_SESSION_ID)
        session = Session(session_config)
        session.get_user(req)

    # get_user() with invalid user
    backup_user = env.request.user

    with pytest.raises(SessionInvalid):
        req = deepcopy(env.request.web)
        env.request.user = User('test')
        session.get_user(req)

    env.request.user = backup_user

    # get_user() with changed backend
    backup_auth = env.auth

    with pytest.raises(SessionInvalid):
        req = deepcopy(env.request.web)
        clean_sessions()
        create_session(env.request.user, session_id=TEST_SESSION_ID)
        env.auth = FakeAuthBackend(ConfigSection(""))
        session.get_user(req)

    env.auth = backup_auth

    # logout()
    with pytest.raises(SessionInvalid):
        clean_sessions()
        create_session(env.request.user, session_id=TEST_SESSION_ID)
        session = Session(session_config)
        req = deepcopy(env.request.web)
        session.logout(req)

    # can_logout()
    assert session.can_logout()

    clean_sessions()
