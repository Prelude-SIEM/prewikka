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
Tests for `prewikka.views.usermanagement`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from prewikka import localization
from prewikka.error import PrewikkaUserError
from tests.utils.fixtures import load_view_for_fixtures


def test_display():
    """
    Test `prewikka.views.usermanagement.display` view.
    """
    view = load_view_for_fixtures("usersettings.display")
    view.render()


def test_modify():
    """
    Test `prewikka.views.usermanagement.modify` view.
    """
    view = load_view_for_fixtures("usersettings.modify")
    backup_parameters = deepcopy(env.request.parameters)

    # valid
    params = {
        'language': next(iter(localization.get_languages().keys())),
        'timezone': localization.get_timezones()[0],
    }
    env.request.parameters = params

    view.render()

    # FIXME
    # valid with new email
    # params_email = deepcopy(params)
    # params_email['email'] = 'foo@bar.tld'
    # env.request.parameters = params_email

    # view.render()

    # valid with new theme (reload page)
    params_email = deepcopy(params)
    params_email['theme'] = 'dark'
    env.request.parameters = params_email

    view.render()

    # FIXME
    # valid with different user
    # params_user = deepcopy(params)
    # params_user['name'] = 'test_different'
    # env.request.parameters = params_user

    # view.modify()

    # invalid language
    with pytest.raises(PrewikkaUserError):
        params_invalid = deepcopy(params)
        params_invalid['language'] = None
        env.request.parameters = params_invalid

        view.render()

    # invalid timezone
    with pytest.raises(PrewikkaUserError):
        params_invalid = deepcopy(params)
        params_invalid['timezone'] = None
        env.request.parameters = params_invalid

        view.render()

    # clean
    env.request.parameters = backup_parameters
