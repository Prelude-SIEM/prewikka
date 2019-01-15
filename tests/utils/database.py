# Copyright (C) 2018-2019 CS-SI. All Rights Reserved.
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
Database utils for prewikka tests suite.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import prelude
import preludedb

# FIXME: remove this with pytest 3+, it is used to prevent some encoding (latin-1 for example)
# errors in database messages
prelude.python2_return_unicode(False)

_LIBPRELUDEDB_DEFAULT_SQL_PATH = '/usr/share/libpreludedb/classic/'


def init_idmef_database(config):
    """
    Create IDMEF database.

    :return: prelude SQL object
    :rtype: preludedb.SQL
    """
    sql = preludedb.SQL(dict(config.idmef_database))
    libpreludedb_sql_path = config.libpreludedb.get('sql_path', _LIBPRELUDEDB_DEFAULT_SQL_PATH)

    # create database structure
    sql_file_path = os.path.join(libpreludedb_sql_path, '%s.sql' % config.idmef_database.type)
    with open(sql_file_path, 'r') as sql_file:
        sql.query(sql_file.read())


def clean_database(database):
    """
    Remove all tables in a database.

    :param database: database information from config
    """
    db_type = database.type
    sql = preludedb.SQL(dict(database))

    if db_type == 'pgsql':
        # https://stackoverflow.com/a/36023359
        sql_query = """
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;"""
    elif db_type == 'mysql':
        # http://stackoverflow.com/a/18625545
        sql_query = """
SET FOREIGN_KEY_CHECKS = 0;
SET GROUP_CONCAT_MAX_LEN=32768;
SET @tables = NULL;
SELECT GROUP_CONCAT('`', table_name, '`')
    INTO @tables
    FROM information_schema.tables
    WHERE table_schema = (SELECT DATABASE());
SELECT IFNULL(@tables,'dummy') INTO @tables;
SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables);
PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SET FOREIGN_KEY_CHECKS = 1;"""

    else:
        raise AttributeError('%s is not a valid database type for test suite' % db_type)

    sql.query(sql_query)
