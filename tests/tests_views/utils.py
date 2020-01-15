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
Utils for `prewikka.views` tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import prelude

from prewikka.dataprovider import Criterion


def create_heartbeat(heartbeat_id, heartbeat_date=None, heartbeat_interval=600, status='', analyzer_id=None):
    """
    Create an IDMEF Heartbeat for test suite.

    :param str heartbeat_id: Heartbeat ID.
    :param str heartbeat_date: Optional Heartbeat date.
    :param str heartbeat_interval: default interval.
    :param str status: Add "Analyzer status" in additional data.
    :param str analyzer_id: Analyzer ID, based on heartbeat_id if not specified.
    :return: An IDMEF object with Heartbeat information.
    :rtype: prelude.IDMEF
    """
    if not analyzer_id:
        analyzer_id = heartbeat_id.replace('-', '')

    idmef = prelude.IDMEF()
    if heartbeat_date:
        idmef.set('heartbeat.create_time', heartbeat_date)

    idmef.set('heartbeat.messageid', heartbeat_id)
    idmef.set('heartbeat.heartbeat_interval', heartbeat_interval)
    idmef.set('heartbeat.analyzer(0).analyzerid', analyzer_id)
    idmef.set('heartbeat.analyzer(0).name', 'prelude-testing')
    idmef.set('heartbeat.analyzer(0).manufacturer', 'http://www.prelude-siem.com')
    idmef.set('heartbeat.analyzer(0).node.name', 'testing.prelude')
    idmef.set('heartbeat.additional_data(0).meaning', 'Analyzer status')
    idmef.set('heartbeat.additional_data(0).data', status)

    return idmef


def delete_heartbeat(heartbeat_id):
    """
    Delete a Heartbeat in database after tests.

    :param str heartbeat_id: Heartbeat ID.
    :type heartbeat_id: str
    :return: None.
    """
    env.dataprovider.delete(Criterion('heartbeat.messageid', '=', heartbeat_id))


def get_heartbeat(heartbeat_id):
    """
    Delete a Heartbeat in database after tests.

    :param str heartbeat_id: Heartbeat ID.
    """
    return env.dataprovider.get(Criterion('heartbeat.messageid', '=', heartbeat_id))


def create_alert(alert_id):
    """
    Create an IDMEF Alert for test suite.

    :param str alert_id: Alert ID.
    :return: An IDMEF object with alert information.
    :rtype: prelude.IDMEF
    """
    idmef = prelude.IDMEF()
    idmef.set('alert.messageid', alert_id)
    idmef.set('alert.analyzer(0).analyzerid', alert_id.replace('-', ''))
    idmef.set('alert.analyzer(0).name', 'prelude-testing')
    idmef.set('alert.analyzer(0).manufacturer', 'http://www.prelude-siem.com')
    idmef.set('alert.analyzer(0).node.name', 'testing.prelude')

    return idmef


def get_alert(alert_id):
    """
    Get an alert for test suite.

    :param str alert_id: Alert ID.
    :return: alert if exists.
    :rtype: prewikka.utils.misc.CachingIterator
    """
    return env.dataprovider.get(Criterion('alert.messageid', '=', alert_id))


def create_correlation_alert(alert_id, correlation_name, correlated_alertid='correlated_alert_ident'):
    """
    Create a correlation alert for test suite.

    :param str alert_id: Alert ID.
    :param str correlation_name: alert.correlation_alert.name IDMEF value.
    :return: An IDMEF object with correlation alert information.
    :rtype: prelude.IDMEF
    """
    idmef = create_alert(alert_id)
    idmef.set('alert.correlation_alert.name', correlation_name)
    idmef.set('alert.correlation_alert.alertident(0).alertident', correlated_alertid)

    return idmef
