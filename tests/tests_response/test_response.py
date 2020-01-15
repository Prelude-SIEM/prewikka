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
Tests for `prewikka.response`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import OrderedDict
from copy import deepcopy
import os

from prewikka.response import PrewikkaResponse, PrewikkaDownloadResponse, PrewikkaFileResponse, PrewikkaRedirectResponse
from tests.utils.vars import TEST_DATA_DIR


class FakeJsonObjClass(object):
    """
    Fake class with __json__ att for test suite.
    """
    foobar = 'bar'

    def __json__(self):
        return {'foo': self.foobar}


def test_prewikka_response():
    """
    Test `prewikka.response.PrewikkaResponse` class.
    """
    response = PrewikkaResponse()

    # response with specifics headers
    headers = OrderedDict(
        (
            ("Content-Type", "text/html"),
            ("Foo", "Bar")
        )
    )
    response_with_headers = PrewikkaResponse(headers=headers, data='Tests !')

    # empty content
    assert response.content() is None

    # add_ext_content()
    response.add_ext_content('foo', 'bar')

    # add_notification()
    response.add_notification('message')

    # content()
    assert response.content() is not None
    assert response_with_headers.content() == 'Tests !'

    # content() with XHR
    env.request.web.is_xhr = True
    response_xhr = PrewikkaResponse(data={'foo': 'bar'})

    assert '"foo": "bar"' in response_xhr.content()

    response_xhr_2 = PrewikkaResponse(data='foobar')

    assert response_xhr_2.content() == 'foobar'

    fooo = FakeJsonObjClass()
    response_xhr_3 = PrewikkaResponse(data=fooo)

    assert response_xhr_3.content() == '{"foo": "bar"}'

    env.request.web.is_xhr = False  # clean

    # write()
    req = deepcopy(env.request.web)
    response.write(req)


def test_prewikka_download_response():
    """
    Test `prewikka.response.PrewikkaDownloadResponse` class.
    """
    # valid file
    response = PrewikkaDownloadResponse('', filename='test.txt')
    response.write(env.request.web)

    # invalid file
    response2 = PrewikkaDownloadResponse('', filename='test')
    response2.write(env.request.web)

    # true file (not str)
    with open(os.path.join(TEST_DATA_DIR, 'file.txt')) as test_file:
        response3 = PrewikkaDownloadResponse(test_file, filename='test.txt')
        response3.write(env.request.web)

    # other possibilities
    response4 = PrewikkaDownloadResponse('', filename='test.jpg', type='image/jpeg')
    response4.write(env.request.web)

    response5 = PrewikkaDownloadResponse('')
    response5.write(env.request.web)

    response6 = PrewikkaDownloadResponse('', size=42)
    response6.write(env.request.web)


def test_prewikka_file_response():
    """
    Test `prewikka.response.PrewikkaFileResponse` class.
    """
    path = os.path.join(TEST_DATA_DIR, 'file.txt')
    backup_headers = deepcopy(env.request.web.headers)

    # default response
    response = PrewikkaFileResponse(path)
    response.write(env.request.web)

    # modified-since
    env.request.web.headers['if-modified-since'] = '2012-01-19 17:21:00 UTC'
    response2 = PrewikkaFileResponse(path)
    response2.write(env.request.web)

    # modified-since + 304 code
    env.request.web.headers['if-modified-since'] = '2030-01-19 17:21:00 UTC'
    response3 = PrewikkaFileResponse(path)
    response3.write(env.request.web)

    # clean
    env.request.web.headers = backup_headers


def test_prewikka_redirect_response():
    """
    Test `prewikka.response.PrewikkaRedirectResponse` class.
    """
    response = PrewikkaRedirectResponse('https://google.com')

    assert response.code == 302
