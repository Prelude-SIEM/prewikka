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
Tests for `prewikka.mainmenu`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime

import pytest

from prewikka.mainmenu import HTMLMainMenu, MainMenuStep, TimeUnit, TimePeriod, _MainMenu
from prewikka.view import GeneralParameters
from tests.utils.fixtures import load_view_for_fixtures


@pytest.fixture(scope='function')
def mainmenu_fixtures(request):
    """
    Fixture for `prewikka.mainmenu` test.
    """
    backup_parameters = env.request.parameters

    view = load_view_for_fixtures('BaseView.render')

    env.request.parameters['orderby'] = None
    env.request.parameters['timeline_mode'] = 'relative'
    env.request.parameters['timeline_value'] = 12
    env.request.parameters['timeline_unit'] = 'day'
    env.request.parameters['auto_apply_value'] = None

    def tear_down():
        """
        TearDown.
        """
        env.request.parameters = backup_parameters

    request.addfinalizer(tear_down)

    return {'view': view}


def test_mainmenu_parameters():
    """
    Test `prewikka.view.GeneralParameters` class.
    """
    view = load_view_for_fixtures('BaseView.render')
    mainmenu = GeneralParameters(view, {})
    mainmenu.register()
    mainmenu.normalize()


def test_time_unit():
    """
    Test `prewikka.mainmenu.TimeUnit` class.
    """
    time_unit = TimeUnit(0)
    time_unit2 = TimeUnit(3)
    time_unit3 = TimeUnit('year')

    with pytest.raises(Exception):
        TimeUnit(-2)

    with pytest.raises(Exception):
        TimeUnit(10101010)

    assert time_unit != time_unit2
    assert not time_unit == time_unit2

    t_unit = time_unit + 1

    assert int(t_unit) == 1

    t_unit = time_unit2 - 1

    assert int(t_unit) == 2
    assert time_unit > time_unit2
    assert time_unit >= time_unit2
    assert time_unit2 < time_unit
    assert time_unit2 <= time_unit

    with pytest.raises(AssertionError):
        assert time_unit.dbunit == 12

    assert time_unit3.dbunit == 'year'


def test_mainmenu_step():
    """
    Test `prewikka.mainmenu.MainMenuStep` class.
    """
    MainMenuStep('year', 2)
    MainMenuStep('month', 1)

    with pytest.raises(KeyError):
        MainMenuStep('seconds', 59)


def test_html_mainmenu(mainmenu_fixtures):
    """
    Test `prewikka.mainmenu.HTMLMainMenu` class.
    """
    # custom parameters
    parameters = {
        'timeline_value': 0,
        'timeline_start': 1234567890,
        'timeline_end': 1234567890 + 3600*48  # add 48h
    }
    HTMLMainMenu(**parameters)

    # auto_apply_value
    parameters['auto_apply_value'] = 300
    HTMLMainMenu(**parameters)

    # test dataset.quick in class
    parameters = {
        'timeline_value':  1,
        'timeline_unit': 'month',
        'timeline_mode': 'absolute'
    }
    HTMLMainMenu(**parameters)


def test_mainmenu_get_parameters(mainmenu_fixtures):
    """
    Test `prewikka.mainmenu._MainMenu.get_parameters()` method.
    """
    main_menu = _MainMenu()
    assert main_menu.get_parameters()


def test_timeperiod_get_step(mainmenu_fixtures):
    """
    Test `prewikka.mainmenu.TimePeriod.get_step()` method.
    """
    parameters = {'timeline_mode': 'relative', 'timeline_value': 2}

    # year
    parameters['timeline_unit'] = 'year'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'month'

    # month
    parameters['timeline_unit'] = 'month'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'day'

    # day
    parameters['timeline_unit'] = 'day'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'hour'

    # hour
    parameters['timeline_unit'] = 'hour'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'minute'

    # minute
    parameters['timeline_unit'] = 'minute'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'minute'

    # second (-> minutes)
    parameters['timeline_unit'] = 'second'
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'minute'

    # 10 days
    parameters['timeline_unit'] = 'day'
    parameters['timeline_value'] = 10
    period = TimePeriod(parameters)
    assert period.get_step(100).unit == 'day'


def test_timeperiod_mktime_param(mainmenu_fixtures):
    """
    Test `prewikka.mainmenu.TimePeriod.mktime_param()` method.
    """
    period = TimePeriod(env.request.menu_parameters)
    datetime_ = datetime(year=2001, month=2, day=3, hour=4, minute=5, second=6)

    assert period.mktime_param(datetime_) == 981173106
    assert period.mktime_param(datetime_, precision=2) == 980985600
    assert period.mktime_param(datetime_, precision=1000) == 981173106


def test_timeperiod_get_criteria(mainmenu_fixtures):
    """
    Test `prewikka.mainmenu.TimePeriod.get_criteria()` method.
    """
    parameters = env.request.menu_parameters

    # no start/end
    period = TimePeriod(parameters)
    assert period.get_criteria()

    # start only
    period = TimePeriod(dict(parameters, timeline_start=123456789))
    assert period.get_criteria()

    # end only
    period = TimePeriod(dict(parameters, timeline_end=123456789))
    assert period.get_criteria()

    # both
    period = TimePeriod(dict(parameters, timeline_start=123456789, timeline_end=123456789))
    assert period.get_criteria()
