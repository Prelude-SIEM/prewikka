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
Tests for `prewikka.utils.html`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.utils.html import escape, escapejs
from prewikka.utils.html.helpers import selected, checked, disabled


def test_escape():
    """
    Test `prewikka.utils.html.escape()`.
    """
    assert text_type(escape(None)) == ''
    assert text_type(escape('')) == ''
    assert text_type(escape('foo')) == 'foo'
    assert text_type(escape('foo bar')) == 'foo bar'
    assert text_type(escape('<script>alert();</script>')) == '&lt;script&gt;alert();&lt;/script&gt;'


def test_escapejs():
    """
    Test `prewikka.utils.html.escapejs()`.
    """
    assert text_type(escapejs('')) == '""'
    assert text_type(escapejs('foo')) == '"foo"'
    assert text_type(escapejs('foo bar')) == '"foo bar"'
    assert text_type(escapejs('<script>alert();</script>')) == '"\\u003cscript\\u003ealert();\\u003c/script\\u003e"'


def test_selected():
    """
    Test `prewikka.utils.html.selected()`.
    """
    assert selected('') == ''
    assert selected('foo') == 'selected'
    assert selected(False) == ''
    assert selected(True) == 'selected'


def test_checked():
    """
    Test `prewikka.utils.html.checked()`.
    """
    assert checked('') == ''
    assert checked('foo') == 'checked'
    assert checked(False) == ''
    assert checked(True) == 'checked'


def test_disabled():
    """
    Test `prewikka.utils.html.disabled()`.
    """
    assert disabled('') == ''
    assert disabled('foo') == 'disabled'
    assert disabled(False) == ''
    assert disabled(True) == 'disabled'
