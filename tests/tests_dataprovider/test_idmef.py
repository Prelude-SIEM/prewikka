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
Tests for `prewikka.dataprovider.idmef`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import prelude

from prewikka.dataprovider import Criterion
from prewikka.dataprovider.idmef import _IDMEFProvider, IDMEFAlertProvider, IDMEFHeartbeatProvider


def test_idmef_provider():
    """
    Test `prewikka.dataprovider.idmef._IDMEFProvider()` class.
    """
    provider = _IDMEFProvider()

    assert provider.get_path_type('alert.classification.text') is text_type
    assert provider._get_paths(prelude.IDMEFClass('alert.classification'))


def test_idmef_alert_provider():
    """
    Test `prewikka.dataprovider.idmef.IDMEFAlertProvider` class.
    """
    alert_provider = IDMEFAlertProvider()

    assert alert_provider.get_path_type('alert.classification.text')
    assert alert_provider.get_paths()
    assert alert_provider.get_common_paths()
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '<>', 'foo'))
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '<>', '*'))
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '=', None))


def test_idemf_heartbeat_provider():
    """
    Test `prewikka.dataprovider.idmef.IDMEFHeartbeatProvider` class.
    """
    heartbeat_provider = IDMEFHeartbeatProvider()

    assert heartbeat_provider.get_path_type('alert.classification.text')
    assert heartbeat_provider.get_paths()
