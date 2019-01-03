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
Tests for `prewikka.utils.timeutil`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

from prewikka.utils import timeutil


class UTC(datetime.tzinfo):
    """
    TimeZone with UTC.
    """
    def utcoffset(self, datetime_):
        return datetime.timedelta(0)

    def tzname(self, datetime_):
        return 'UTC'

    def dst(self, datetime_):
        return datetime.timedelta(0)


def test_now():
    """
    Test `prewikka.utils.timeutil.now()`.
    """
    assert timeutil.now()


def test_utcnow():
    """
    Test `prewikka.utils.timeutil.utcnow()`.
    """
    assert timeutil.utcnow().ctime() == datetime.datetime.now(tz=UTC()).ctime()


def test_get_timestamp_from_str():
    """
    Test `prewikka.utils.timeutil.get_timestamp_from_string()`.
    """
    assert not timeutil.get_timestamp_from_string(None)
    assert not timeutil.get_timestamp_from_string('1973-11-28 21:33:09') == 123456789


def test_get_timestamp_from_dt():
    """
    Test `prewikka.utils.timeutil.get_timestamp_from_datetime()`.
    """
    datetime_ = datetime.datetime(year=1973, month=11, day=28, hour=21, minute=33, second=9, tzinfo=UTC())

    assert timeutil.get_timestamp_from_datetime(datetime_) == 123370389
