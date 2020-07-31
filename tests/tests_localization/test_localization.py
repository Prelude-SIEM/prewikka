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
Tests for `prewikka.localization`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime, time, timedelta
import os

import pytest

from prewikka import utils
from prewikka.localization import translation, set_locale, get_languages, \
    get_current_charset, format_date, format_time, format_datetime, format_timedelta, \
    format_number, get_period_names, get_day_names, get_month_names, get_quarter_names, get_era_names, \
    get_calendar_format, get_timezones, get_system_timezone
from tests.utils.vars import TEST_DATA_DIR


def test_translation_proxy():
    """
    Test `prewikka.localization.TranslationProxy()` class.
    """
    # get_charset() (with translation._data empty)
    assert translation.get_charset().lower() == 'utf-8'

    # get_locale() (with translation._data empty)
    assert 'en_GB' in translation.get_locale()

    # set_locale()
    translation.set_locale('fr_FR')

    assert translation.get_locale() == 'fr_FR'

    # gettext
    assert translation.gettext('foo') == 'foo'

    # ngettext
    assert translation.ngettext('foo', 'foos', 0) == 'foos'
    assert translation.ngettext('foo', 'foos', 1) == 'foo'
    assert translation.ngettext('foo', 'foos', 42) == 'foos'

    # add_domain()
    assert len(translation._domains) == 1

    domain = 'prewikka_test'
    path = os.path.join(TEST_DATA_DIR, 'locale')
    translation.add_domain(domain, path)

    assert translation._domains[domain] == path
    assert len(translation._domains) == 2

    del translation._domains[domain]  # clean

    # clean
    translation.set_locale('en_GB')

    assert translation.get_locale() == 'en_GB'


def test_set_locale():
    """
    Test `prewikka.localization.set_locale()` function.
    """
    assert translation.get_locale() == 'en_GB'

    set_locale('fr_FR')

    assert translation.get_locale() == 'fr_FR.UTF-8'

    set_locale(None)

    assert translation.get_locale() == 'en_GB.UTF-8'

    # clean
    translation.set_locale('en_GB')

    assert translation.get_locale() == 'en_GB'


def test_get_languages():
    """
    Test `prewikka.localization.get_languages()` function.
    """
    assert 'en_GB' in get_languages()


def test_get_current_charset():
    """
    Test `prewikka.localization.get_current_charset()` function.
    """
    assert get_current_charset().lower() == 'utf-8'


def test_format_date():
    """
    Test `prewikka.localization.format_date()` function.
    """
    # datetime
    test_date = datetime(year=1985, month=10, day=26, tzinfo=utils.timeutil.tzutc())

    assert format_date(test_date) == '26 Oct 1985'

    test_date = datetime(year=1985, month=10, day=26, hour=21, minute=0, tzinfo=utils.timeutil.tzutc())

    assert format_date(test_date, tzinfo=utils.timeutil.tzutc()) == '26 Oct 1985'

    # int
    assert format_date(499151337) == '26 Oct 1985'
    assert format_date(499151337, tzinfo=utils.timeutil.tzutc()) == '26 Oct 1985'


def test_format_time():
    """
    Test `prewikka.localization.format_time() function`.
    """
    # time
    test_time = time(hour=10, minute=10, second=10).replace(tzinfo=utils.timeutil.tzutc())

    assert format_time(test_time) == '10:10:10'
    assert format_time(test_time, tzinfo=utils.timeutil.tzutc()) == '10:10:10'

    # int
    assert format_time(10*3600 + 10*60 + 10) == '11:10:10'  # UTC+1
    assert format_time(10*3600 + 10*60 + 10, tzinfo=utils.timeutil.tzutc()) == '10:10:10'


def test_format_datetime():
    """
    Test `prewikka.localization.format_datetime()` function.
    """
    # datetime
    test_datetime = datetime(year=1985, month=10, day=26, hour=20, minute=0).replace(tzinfo=utils.timeutil.tzutc())

    assert format_datetime(test_datetime) == '26 Oct 1985 21:00:00'  # UTC+1

    test_date = datetime(year=1985, month=10, day=26, hour=21, minute=0, tzinfo=utils.timeutil.tzutc())

    assert format_date(test_date, tzinfo=utils.timeutil.tzutc()) == '26 Oct 1985'

    # int
    assert format_datetime(499204800) == '26 Oct 1985 21:00:00'  # UTC+1
    assert format_datetime(499204800, tzinfo=utils.timeutil.tzutc()) == '26 Oct 1985 20:00:00'


@pytest.mark.xfail(reason='babel update required')
def test_format_timedelta():
    """
    Test `prewikka.localization.format_timedelta()` function.
    """
    assert format_timedelta(timedelta(hours=0)) == '0 seconds'
    assert format_timedelta(timedelta(hours=4)) == '4 hours'
    assert format_timedelta(timedelta(hours=42)) == '2 days'


@pytest.mark.xfail(reason='babel update required')
def test_format_number():
    """
    Test `prewikka.localization.format_number()` function.
    """
    assert format_number(0) == '0'
    assert format_number(42) == '42'
    assert format_number(1337) == '1,337'
    assert format_number(1123581321345589144) == '1,123,581,321,345,589,144'
    assert format_number(13.37) == '13.37'
    assert format_number(1010.10) == '1,010.1'


def test_get_period_names():
    """
    Test `prewikka.localization.get_period_name()` function.
    """
    assert get_period_names()


def test_get_day_names():
    """
    Test `prewikka.localization.get_day_names()` function.
    """
    assert get_day_names()


def test_get_month_names():
    """
    Test `prewikka.localization.get_month_names()` function.
    """
    assert get_month_names()


def test_get_quarter_names():
    """
    Test `prewikka.localization.get_quarter_names()` function.
    """
    assert get_quarter_names()


def test_get_era_names():
    """
    Test `prewikka.localization.get_era_names()` function.
    """
    assert get_era_names()


def test_get_calendar_format():
    """
    Test `prewikka.localization.get_calendar_format()` function.
    """
    assert get_calendar_format() == 'dd/mm/yy'


def test_get_timezones():
    """
    Test `prewikka.localization.get_timezones()` function.
    """
    assert len(get_timezones()) != 0


def test_get_system_timezone():
    """
    Test `prewikka.localization.get_system_timezone()` function.
    """
    assert get_system_timezone()
