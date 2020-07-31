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
Tests for `prewikka.dataprovider` except Criteron() class.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime

import pytest

from prewikka.dataprovider import to_datetime, ResultObject
from prewikka.error import PrewikkaUserError
from prewikka.utils.timeutil import tzutc


def test_to_datetime():
    """
    Test `prewikka.dataprovider.to_datetime` function.
    """
    correct_datetime = datetime.datetime(1973, 11, 29, 21, 33, 9, tzinfo=tzutc())

    assert to_datetime(123456789) == correct_datetime
    assert to_datetime(123456789.3) == correct_datetime.replace(microsecond=300000)
    assert to_datetime('123456789') == correct_datetime
    assert to_datetime('1973-11-29 21:33:09 UTC') == correct_datetime
    assert to_datetime('1973-11-29 21:33:09') == correct_datetime
    assert to_datetime(correct_datetime) == correct_datetime
    assert not to_datetime(None)

    with pytest.raises(PrewikkaUserError):
        to_datetime({})


def test_result_object():
    """
    Test `prewikka.dataprovider.ResultObject` class.
    """
    result = ResultObject({'foo': 'bar', '42': 42})

    assert result.preprocess_value('foobar') == 'foobar'
