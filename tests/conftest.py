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
Configuration file for pytest.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys

import pytest

from tests.fixtures import initialization_fixtures, prewikka_fixtures  # noqa


_PYTHON = sys.version_info
_PYTEST_SKIP_MESSAGE = 'Test skipped due to %s: %s (system) != %s (test requirement)'


def _check_py_markers(markers):
    """
    Check markers for python ("py" in name).

    :param list markers: list of all markers on a test.
    """
    py_markers = [marker for marker in markers if 'py' in marker]

    if not py_markers:
        return

    py_major_marker = 'py%d_only' % _PYTHON.major
    py_major_minor_marker = 'py%d%d_only' % (_PYTHON.major, _PYTHON.minor)
    if py_major_marker not in py_markers and py_major_minor_marker not in py_markers:
        # formatting skip message
        python_test_version = py_markers[0].split('_')[0][2:]
        if len(python_test_version) == 1:  # 2 or 3 (not 2.7, 3.0, 3.1...)
            python_sys_version = '%d' % _PYTHON.major
        else:
            python_sys_version = '%d.%d' % (_PYTHON.major, _PYTHON.minor)
        pytest_message = _PYTEST_SKIP_MESSAGE % ('python version', python_sys_version, python_test_version)
        pytest.skip(pytest_message)


def _check_sql_markers(markers):
    """
    Check markers for SQL engines ("sql" in name).

    :param list markers: list of all markers on a test.
    """
    db_type = env.config.database.type
    sql_markers = [marker for marker in markers if 'sql' in marker]

    if not sql_markers:
        return

    sql_marker = '%s_only' % db_type
    if sql_marker not in sql_markers:
        pytest.skip(_PYTEST_SKIP_MESSAGE % ('sql engine', db_type, sql_markers[0].split('_')[0]))


def pytest_runtest_setup(item):
    """
    Pytest hook run before each test to skip specified tests.

    - Python version is checked and all tests with "@pytest.mark.py<x>_only" and "@pytest.mark.py<x><y>_only" they
    do not match with current Python version are skipped.
    - SQL engine is checked based on prewikka configuration file using during tests.

    Supported markers:
        - py<x>_only            where <x> is major version of Python (ex: py2_only)
        - py<x><y>_only         where <x> is major version of Python and <y> minor version (ex: py36_only)
        - mysql_only            MySQL/MariaDB only
        - pgsql_only            PostgreSQL only
        - sqlite_only           SQLte3 only

    Multiple markers are supported for Python markers. They are NOT exclusive. Example:

        @pytest.mark.mysql_only
        @pytest.mark.py26_only
        @pytest.mark.py27_only
        def test_foo():
            pass

    This test will run only with python 2.6 or 2.7 and with MySQL engine.
    """
    if isinstance(item, item.Function):
        # get all markers with "_only" in name
        markers = [marker for marker in item.keywords.keys() if '_only' in marker]
        if markers:
            _check_py_markers(markers)
            _check_sql_markers(markers)
