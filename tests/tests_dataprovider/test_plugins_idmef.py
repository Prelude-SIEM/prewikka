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
Tests for `prewikka.dataprovider.plugins.idmef`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime

from prelude import IDMEFTime

from prewikka.dataprovider.plugins.idmef import IDMEFResultObject


def test_idmef_result_object():
    """
    Test `prewikka.dataprovider.plugins.idmef.IDMEFResultObject()` class.
    """
    res = IDMEFResultObject(None)

    assert res.preprocess_value(12) == 12
    assert res.preprocess_value('12') == '12'
    assert res.preprocess_value(IDMEFTime(12)).replace(tzinfo=None) == datetime(1970, 1, 1, 1, 0, 12)
