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
Tests for `prewikka.compat`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest


@pytest.mark.py2_only
def test_compat_basestring():
    """
    Test `prewikka.compat.STRING_TYPES` import, Python 2 version.
    """
    from prewikka.compat import STRING_TYPES

    assert isinstance(b"foo", STRING_TYPES)
    assert isinstance(u"bar", STRING_TYPES)


@pytest.mark.py3_only
def test_compat_str():
    """
    Test `prewikka.compat.STRING_TYPES` import, Python 3 version.
    """
    from prewikka.compat import STRING_TYPES

    assert not isinstance(b"foo", STRING_TYPES)
    assert isinstance(u"bar", STRING_TYPES)
