# Copyright (C) 2018 CS-SI. All Rights Reserved.
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
Tests for `prewikka.utils.misc`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.dataprovider import Criterion
from prewikka.utils import misc, json
from tests.tests_views.utils import create_heartbeat, delete_heartbeat


@misc.deprecated
def fake_depreciated_function():
    """
    Fake function used in tests.
    :return: 42
    """
    return 42


def test_attr_obj():
    """
    Test `prewikka.utils.misc.AttrObj()`.
    """
    attr1 = misc.AttrObj()
    attr2 = misc.AttrObj(foo=12, bar=list())

    assert attr1
    assert attr2

    assert json.dumps(attr1) == '{}'
    assert json.dumps(attr2) == '{"foo": 12, "bar": []}'

    assert not attr1 == attr2


def test_get_analyzer_status():
    """
    Test `prewikka.utils.misc.get_analyzer_status_from_latest_heartbeat()`.
    """
    heartbeat_id = 'NqnYbirynpr'
    idmef_db = env.dataprovider._backends["alert"]._db
    criteria = Criterion('heartbeat.messageid', '=', heartbeat_id)

    heartbeats = [
        (create_heartbeat(heartbeat_id, status='exiting'), 'offline'),
        (create_heartbeat(heartbeat_id, heartbeat_interval=None), 'unknown'),
        (create_heartbeat(heartbeat_id, heartbeat_date='1991-08-25 20:57:08'), 'missing'),
        (create_heartbeat(heartbeat_id), 'online')
    ]

    for idmef, expected_status in heartbeats:
        idmef_db.insert(idmef)
        heartbeat = env.dataprovider.get(criteria)[0]['heartbeat']
        status = misc.get_analyzer_status_from_latest_heartbeat(heartbeat, 0)

        assert status[0] == expected_status

        delete_heartbeat(heartbeat_id)


def test_protocol_number_to_name():
    """
    Test `prewikka.utils.misc.protocol_number_to_name()`.
    """
    assert misc.protocol_number_to_name(42) == 'sdrp'
    assert misc.protocol_number_to_name(80) == 'iso-ip'
    assert misc.protocol_number_to_name(139) == 'hip'
    assert not misc.protocol_number_to_name(300)


def test_name_to_path():
    """
    Test `prewikka.utils.misc.nameToPath()`.
    """
    assert misc.nameToPath(None) == 'none'
    assert misc.nameToPath('foo') == 'foo'
    assert misc.nameToPath('foo bar') == 'foo_bar'
    assert misc.nameToPath('foo_bar') == 'foo_bar'
    assert misc.nameToPath(42) == '42'
    assert misc.nameToPath(3.14) == '3.14'


def test_find_unescaped_characters():
    """
    Test `prewikka.utils.misc.find_unescaped_characters()`.
    """
    assert not misc.find_unescaped_characters('foo')
    assert misc.find_unescaped_characters('foo', 'o')
    assert not misc.find_unescaped_characters('foo', 'a')
    assert not misc.find_unescaped_characters('foo\\bar', 'b')


def test_split_unescaped_characters():
    """
    Test `prewikka.utils.misc.split_unescaped_characters()`.
    """
    res = misc.split_unescaped_characters('foo', '')

    assert next(res) == 'foo'

    res = misc.split_unescaped_characters('foo bar', ' ')

    assert next(res) == 'foo'
    assert next(res) == 'bar'

    res = misc.split_unescaped_characters('foobar', 'o')

    assert next(res) == 'f'
    assert next(res) == ''
    assert next(res) == 'bar'

    res = misc.split_unescaped_characters('foobar', 'oo')

    assert next(res) == 'f'
    assert next(res) == ''
    assert next(res) == 'bar'

    res = misc.split_unescaped_characters('foo\\bar', 'b')

    assert next(res) == 'foo\\bar'

    res = misc.split_unescaped_characters('foo;bar', [';'])

    assert next(res) == 'foo'
    assert next(res) == 'bar'


def test_soundex():
    """
    Test `prewikka.utils.misc.soundex()`.
    """
    assert misc.soundex('Prewikka') == 'P62'
    assert misc.soundex('Prelude') == 'P643'
    assert misc.soundex('foobar') == 'F16'


def test_hexdump():
    """
    Test `prewikka.utils.misc.hexdump()`.
    """
    assert misc.hexdump('Prewikka') == '0000:    50 72 65 77 69 6b 6b 61                            Prewikka\n'
    assert misc.hexdump('Prelude') == '0000:    50 72 65 6c 75 64 65                               Prelude\n'
    assert misc.hexdump('foobar') == '0000:    66 6f 6f 62 61 72                                  foobar\n'


def test_depreciated():
    """
    Test `prewikka.utils.misc.deprecated()`.
    """
    # just call the function
    assert fake_depreciated_function() == 42


def test_caching_iterator():
    """
    Test `prewikka.utils.misc.CachingIterator()`.
    """
    iterator1 = misc.CachingIterator(['foo', 'bar', 42])
    iterator2 = misc.CachingIterator(['foo', 'bar', 42], 3)

    # len()
    assert len(iterator1) == 3
    assert len(iterator2) == 3

    # preprocess_value()
    assert iterator1.preprocess_value(12) == 12
    assert not iterator2.preprocess_value(None)

    # __iter__
    assert list(iterator1)
    assert list(iterator1)  # second time use cache

    # __getitems__
    assert iterator1[0] == 'foo'
    assert iterator1[0:1] == ['foo']
    assert iterator1[0:2] == ['foo', 'bar']
    assert iterator1[1] == 'bar'
    assert iterator1[2] == 42

    with pytest.raises(IndexError):
        assert iterator1[3]

    assert iterator2[0] == 'foo'
    assert iterator2[1] == 'bar'
    assert iterator2[0:1] == ['foo']
    assert iterator2[0:2] == ['foo', 'bar']
    assert iterator2[2] == 42

    with pytest.raises(IndexError):
        assert iterator2[3]
