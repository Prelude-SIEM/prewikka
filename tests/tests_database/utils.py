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
Utils for `prewikka.database` tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.database import SQLScript


class SQLScriptTest(SQLScript):
    """
    Fake class for test suite.
    """
    version = 42

    def run(self):
        pass


class SQLScriptTestWithBranch(SQLScript):
    """
    Fake class for test suite.
    """
    version = 42
    type = 'branch'
    branch = 'new_branch'
    from_branch = 'old_branch'

    def run(self):
        pass


class SQLScriptTestInstall(SQLScript):
    """
    Fake class for test suite.
    """
    version = 42
    type = 'install'

    def run(self):
        pass


class SQLScriptTestWithoutVersion(SQLScript):
    """
    Fake class for test suite.
    """
    def run(self):
        pass


class SQLScriptTestWithoutFromBranch(SQLScript):
    """
    Fake class for test suite.
    """
    version = 42
    type = 'branch'

    def run(self):
        pass
