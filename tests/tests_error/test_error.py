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
Tests for `prewikka.error`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.error import RedirectionError, PrewikkaError, PrewikkaUserError, NotImplementedError
from prewikka.template import PrewikkaTemplate


def test_redirection_error():
    """
    Test `prewikka.error.RedirectionError` error.
    """
    error = RedirectionError('/', 302)

    with pytest.raises(RedirectionError):
        raise error

    assert error.respond()


def test_prewikka_error():
    """
    Test `prewikka.error.PrewikkaError` error.
    """
    error = PrewikkaError('An error occurred !')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # empty message
    error = PrewikkaError('')

    with pytest.raises(PrewikkaError):
        raise error

    assert not str(error)
    assert error.respond()

    # name
    error = PrewikkaError('An error occurred !', name='Unknown error')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # details
    error = PrewikkaError('An error occurred !', details='Some details about the error.')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # log_priority
    error = PrewikkaError('An error occurred !', log_priority=40)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # log_user
    error = PrewikkaError('An error occurred !', log_user='john')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # template
    template = PrewikkaTemplate('prewikka', 'templates/baseview.mak')
    error = PrewikkaError('An error occurred !', template=template)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # code
    error = PrewikkaError('An error occurred !', code=503)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # traceback disabled then enabled
    backup_traceback = env.config.general.get('enable_error_traceback')
    env.config.general.enable_error_traceback = 'no'
    error = PrewikkaError('An error occurred !', template=template)
    env.config.general.enable_error_traceback = backup_traceback

    assert error.respond()

    # env.request.web.is_stream
    env.request.web.is_stream = not env.request.web.is_stream
    error = PrewikkaError('An error occurred !', template=template)

    assert error.respond()

    env.request.web.is_stream = not env.request.web.is_stream


def test_prewikka_user_error():
    """
    Test `prewikka.error.PrewikkaUserError` error.
    """
    # default
    error = PrewikkaUserError()

    with pytest.raises(PrewikkaUserError):
        raise error

    assert not str(error)

    # name
    error = PrewikkaUserError(name='NAME')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert not str(error)  # message is required

    # message
    error = PrewikkaUserError(message='A message')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert str(error)

    # name + message
    error = PrewikkaUserError(name='NAME', message='A message')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert str(error)


def test_not_implemented_error():
    """
    Test `prewikka.error.NotImplementedError` error.
    """
    # default
    error = NotImplementedError()

    with pytest.raises(NotImplementedError):
        raise error

    assert str(error)
