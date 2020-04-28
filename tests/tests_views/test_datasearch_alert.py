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
Tests `prewikka.views.datasearch.alert`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from tests.utils.fixtures import load_view_for_fixtures
from tests.tests_views.utils import create_correlation_alert


@pytest.fixture(scope='function')
def datasearch_fixtures(request):
    """
    Fixture for datasearch tests.

    :return: view for alerts.
    :rtype: prewikka.view.View
    """
    backup_parameters = deepcopy(env.request.parameters)

    view = load_view_for_fixtures(request.param)
    view.process_parameters()

    alert_id = '79e0ce14-46b6-11e7-9ab4'
    correlation_alert = create_correlation_alert(alert_id, 'correlation_alert_1')
    env.dataprovider._backends["alert"]._db.insert(correlation_alert)

    def tear_down():
        """
        TearDown
        """
        env.request.parameters = backup_parameters
        env.dataprovider._backends["alert"]._db.remove('alert.messageid')

    request.addfinalizer(tear_down)

    return view


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.forensic"], indirect=True)
def test_alerts(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` view.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_timeline"], indirect=True)
def test_alerts_timeline(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` timeline.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_table"], indirect=True)
def test_alerts_table(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` table.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_details"], indirect=True)
def test_alerts_details(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` details.
    """
    view = datasearch_fixtures

    env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "correlation_alert_1"}]}'
    view.render()

    with pytest.raises(IndexError):
        env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "foobar"}]}'
        view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_infos"], indirect=True)
def test_alerts_infos(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` details.
    """
    view = datasearch_fixtures

    env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "correlation_alert_1"}]}'
    env.request.parameters["query"] = 'analyzer(0).name <> "prelude-testing"'
    env.request.parameters["field"] = 'analyzer(0).name'
    env.request.parameters["value"] = 'prelude-testing'

    view.render()
