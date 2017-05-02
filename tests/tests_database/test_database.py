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
Tests for `prewikka.database`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.database import DatabaseError, DatabaseSchemaError, DatabaseUpdateHelper
from tests.tests_database.utils import SQLScriptTest, SQLScriptTestWithBranch, SQLScriptTestWithoutVersion, \
    SQLScriptTestWithoutFromBranch, SQLScriptTestInstall


def test_database_error():
    """
    Test `prewikka.database.DatabaseError()` error.
    """
    with pytest.raises(DatabaseError) as e_info:
        raise DatabaseError('test message')

    assert 'test message' in str(e_info)


def test_database_schema_error():
    """
    Test `prewikka.database.DatabaseSchemaError()` error.
    """
    with pytest.raises(DatabaseSchemaError) as e_info:
        raise DatabaseSchemaError('test message')

    assert 'test message' in str(e_info)


def test_sql_script():
    """
    Test `prewikka.database.SQLScript()` class.
    """
    dbup = DatabaseUpdateHelper('test', 0)

    # default
    sql_script = SQLScriptTest(dbup)

    # type = 'branch'
    sql_script_with_branch = SQLScriptTestWithBranch(dbup)

    # type = 'install'
    sql_script_install = SQLScriptTestInstall(dbup)

    # version = None
    with pytest.raises(Exception):
        SQLScriptTestWithoutVersion(dbup)

    # branch != '' but branch_from == ''
    with pytest.raises(Exception):
        SQLScriptTestWithoutFromBranch(dbup)

    assert sql_script._mysql2sqlite('SELECT * FROM foo;') == 'SELECT * FROM foo;'
    assert sql_script._mysql2pgsql('SELECT * FROM foo;') == 'SELECT * FROM foo;'
    assert sql_script._mysqlhandler('input') == 'input'
    assert not sql_script.query('')

    # test apply() method running
    assert not sql_script.apply()
    assert not sql_script_with_branch.apply()
    assert not sql_script_install.apply()

    # test __eq__
    assert not sql_script == sql_script_install
