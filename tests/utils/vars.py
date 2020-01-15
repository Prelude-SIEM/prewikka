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
Utils for prewikka tests suite.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
TEST_DIR = os.path.join(BASE_DIR, 'tests')
TEST_DATA_DIR = os.path.join(TEST_DIR, 'data')
TEST_DOWNLOAD_DIR = os.path.join(TEST_DIR, 'downloads')
TEST_CONFIG_FILE = os.path.join(TEST_DIR, 'conf', 'tests.conf')

TEST_SESSION_ID = 'testid'
