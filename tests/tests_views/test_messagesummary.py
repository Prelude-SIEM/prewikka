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
Tests `prewikka.views.messagesummary.messagesummary`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from tests.utils.fixtures import load_view_for_fixtures
from tests.tests_views.utils import create_alert, create_correlation_alert, create_heartbeat


_heartbeat_id = 'edd972ea-aaaf-11e8-a6e7'
_alert_id = '79e0ce14-46b6-11e7-9ab4'
_correlation_alert_id = 'c9b37c54-bf56-11e5-9602'


@pytest.fixture(scope='module')
def messagesummary_fixtures(request):
    """
    Fixture for messagesummary tests.

    :return: view for messagesummary.
    :rtype: prewikka.view.View
    """
    backup_parameters = deepcopy(env.request.parameters)

    view = load_view_for_fixtures(request.param)
    view.process_parameters()

    heartbeat = create_heartbeat(_heartbeat_id)
    env.dataprovider._backends["heartbeat"]._db.insert(heartbeat)

    alert = create_alert(_alert_id)
    env.dataprovider._backends["alert"]._db.insert(alert)

    correlation_alert = create_correlation_alert(_correlation_alert_id, 'correlation_alert_1', _alert_id)
    env.dataprovider._backends["alert"]._db.insert(correlation_alert)

    def tear_down():
        """
        TearDown
        """
        env.request.parameters = backup_parameters
        env.dataprovider._backends["alert"]._db.remove('alert.messageid')

    request.addfinalizer(tear_down)

    return view


@pytest.mark.parametrize("messagesummary_fixtures", ["HeartbeatSummary.render"], indirect=True)
def test_heartbeat_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.HeartbeatSummary` view.
    """
    view = messagesummary_fixtures
    view.render(messageid=_heartbeat_id)


@pytest.mark.parametrize("messagesummary_fixtures", ["AlertSummary.render"], indirect=True)
def test_alert_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.AlertSummary` view.
    """
    view = messagesummary_fixtures
    view.render(messageid=_alert_id)


@pytest.mark.parametrize("messagesummary_fixtures", ["AlertSummary.render"], indirect=True)
def test_correlation_alert_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.AlertSummary` view with a correlation alert.
    """
    view = messagesummary_fixtures
    view.render(messageid=_correlation_alert_id)
