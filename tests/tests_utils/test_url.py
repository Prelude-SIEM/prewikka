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
Tests for `prewikka.utils.url`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.utils import url


def test_mkdownload():
    """
    Test `prewikka.utils.url.mkdownload()`.
    """
    dl_file = url.mkdownload('test.txt')

    assert dl_file.__json__()['href']

    dl_file = url.mkdownload('test.txt', user=env.request.user)

    assert dl_file.__json__()['href']


def test_iri2uri():
    """
    Test `prewikka.utils.url.iri2uri()`.
    """
    assert url.iri2uri('http://domain.tld/foo bar.html') == 'http://domain.tld/foo%20bar.html'
    assert url.iri2uri('http://domain.tld/foo:bar.html') == 'http://domain.tld/foo:bar.html'
    assert url.iri2uri('HTTP://www.python.org/doc/#') == 'http://www.python.org/doc/'


def test_urlencode():
    """
    Test `prewikka.utils.url.urlencode()`.
    """
    url_encode = url.urlencode([('foo', 1), ('bar', 2), ('42', '&')])

    assert url_encode == 'foo=1&bar=2&42=%26'
