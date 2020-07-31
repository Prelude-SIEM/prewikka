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
Tests for `prewikka.compat.babelcompat`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta

import pytest

from prewikka.compat.babelcompat import format_timedelta


def test_format_timedelta():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function.
    """
    # with integer
    assert format_timedelta(0) == '0 second'
    assert format_timedelta(3) == '3 second'
    assert format_timedelta(31) == '31 second'
    assert format_timedelta(314) == '5 minute'
    assert format_timedelta(3141) == '1 hour'
    assert format_timedelta(31415) == '9 hour'
    assert format_timedelta(314159) == '4 day'
    assert format_timedelta(3141592) == '1 month'
    assert format_timedelta(31415926) == '1 year'
    assert format_timedelta(314159265) == '10 year'
    assert format_timedelta(-3) == '3 second'
    assert format_timedelta(-31) == '31 second'
    assert format_timedelta(-314) == '5 minute'
    assert format_timedelta(-3141) == '1 hour'
    assert format_timedelta(-31415) == '9 hour'
    assert format_timedelta(-314159) == '4 day'
    assert format_timedelta(-3141592) == '1 month'
    assert format_timedelta(-31415926) == '1 year'
    assert format_timedelta(-314159265) == '10 year'

    # with timedelta
    assert format_timedelta(timedelta(seconds=42)) == '42 second'
    assert format_timedelta(timedelta(minutes=42)) == '42 minute'
    assert format_timedelta(timedelta(hours=2)) == '2 hour'
    assert format_timedelta(timedelta(days=2)) == '2 day'
    assert format_timedelta(timedelta(weeks=42)) == '10 month'
    assert format_timedelta(timedelta(seconds=-42)) == '42 second'
    assert format_timedelta(timedelta(minutes=-42)) == '42 minute'
    assert format_timedelta(timedelta(hours=-2)) == '2 hour'
    assert format_timedelta(timedelta(days=-2)) == '2 day'
    assert format_timedelta(timedelta(weeks=-42)) == '10 month'


def test_format_granularity():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `granularity` param.
    """
    assert format_timedelta(3, granularity='minute') == '1 minute'
    assert format_timedelta(31, granularity='minute') == '1 minute'
    assert format_timedelta(314, granularity='minute') == '5 minute'
    assert format_timedelta(3141, granularity='minute') == '1 hour'
    assert format_timedelta(-3, granularity='minute') == '1 minute'
    assert format_timedelta(-31, granularity='minute') == '1 minute'
    assert format_timedelta(-314, granularity='minute') == '5 minute'
    assert format_timedelta(-3141, granularity='minute') == '1 hour'


def test_format_add_direction():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `add_direction` param.
    """
    assert format_timedelta(3, add_direction=True) == 'in 3 second'
    assert format_timedelta(31, add_direction=True) == 'in 31 second'
    assert format_timedelta(314, add_direction=True) == 'in 5 minute'
    assert format_timedelta(3141, add_direction=True) == 'in 1 hour'
    assert format_timedelta(31415, add_direction=True) == 'in 9 hour'
    assert format_timedelta(314159, add_direction=True) == 'in 4 day'
    assert format_timedelta(3141592, add_direction=True) == 'in 1 month'
    assert format_timedelta(31415926, add_direction=True) == 'in 1 year'
    assert format_timedelta(314159265, add_direction=True) == 'in 10 year'
    assert format_timedelta(-3, add_direction=True) == '3 second ago'
    assert format_timedelta(-31, add_direction=True) == '31 second ago'
    assert format_timedelta(-314, add_direction=True) == '5 minute ago'
    assert format_timedelta(-3141, add_direction=True) == '1 hour ago'
    assert format_timedelta(-31415, add_direction=True) == '9 hour ago'
    assert format_timedelta(-314159, add_direction=True) == '4 day ago'
    assert format_timedelta(-3141592, add_direction=True) == '1 month ago'
    assert format_timedelta(-31415926, add_direction=True) == '1 year ago'
    assert format_timedelta(-314159265, add_direction=True) == '10 year ago'


@pytest.mark.xfail(reason='Issue #2515')
def test_format_timedelta_format():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `format` param.
    NOTE: format is not used in function (except for testing).
    """
    assert format_timedelta(3, format='narrow') == '3 second'
    assert format_timedelta(3, format='short') == '3 second'
    assert format_timedelta(3, format='medium') == '3 second'
    assert format_timedelta(3, format='long') == '3 second'

    with pytest.raises(Exception):
        format_timedelta(42, format='unknown')


def test_format_timedelta_threshold():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `threshold` param.
    """
    assert format_timedelta(12, threshold=12) == '12 second'
