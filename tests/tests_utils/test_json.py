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
Tests for `prewikka.utils.json`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime
from StringIO import StringIO

import pytest

from prewikka.dataprovider import Criterion
from prewikka.utils import json


class FakeClass(object):
    """
    Fake class for tests only.
    """
    def __init__(self):
        self.xyz = 1337


def test_json_object():
    """
    Test prewikka.utils.json.JSONObject().
    """
    obj = json.JSONObject()

    assert hasattr(obj, '__jsonobj__')


def test_load():
    """
    Test prewikka.utils.json.load().
    """
    io_stream = StringIO('["streaming API"]')

    assert json.load(io_stream) == ['streaming API']


def test_loads():
    """
    Test prewikka.utils.json.loads().
    """
    assert json.loads('["foo", {"bar": ["baz", null, 1.0, 2]}]') == ['foo', {'bar': ['baz', None, 1.0, 2]}]
    assert json.loads('"\\"foo\\bar"') == '"foo\x08ar'


def test_dump():
    """
    Test prewikka.utils.json.dumps().
    """
    io_stream = StringIO()
    json.dump(['streaming API'], io_stream)

    assert io_stream.getvalue() == '["streaming API"]'


def test_dumps():
    """
    Test prewikka.utils.json.dump().
    """
    assert json.dumps(['foo', {'bar': ['baz', None, 1.0, 2]}]) == '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    assert json.dumps('"foo\x08ar') == '"\\"foo\\bar"'

    # Prewikka objects
    criterion = Criterion('alert.messageid', '=', 'fakemessageid')
    criterion_dumps = json.dumps(criterion)

    assert '{"__prewikka_class__": ["Criterion"' in criterion_dumps
    assert '"operator": "="' in criterion_dumps
    assert '"right": "fakemessageid"' in criterion_dumps
    assert '"left": "alert.messageid"' in criterion_dumps

    # datetime object
    assert json.dumps(datetime(year=2012, month=10, day=12, hour=0, minute=0, second=0)) == \
        '"2012-10-12 00:00:00"'

    # object not JSON serializable
    fake_obj = FakeClass()

    with pytest.raises(TypeError):
        json.dumps(fake_obj)
