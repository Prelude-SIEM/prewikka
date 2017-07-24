# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

from __future__ import absolute_import, division, print_function, unicode_literals

import abc
import collections
import fcntl
import functools
import operator
import pkgutil
import re
import time
import types
from datetime import datetime

import pkg_resources
import preludedb
from prewikka import compat, error, log, utils, version
from prewikka.utils import cache, json


NotNone = object
ModuleInfo = collections.namedtuple("ModuleInfo", ["branch", "version", "enabled"])


class DatabaseError(error.PrewikkaUserError):
    name = N_("Database error")

    def __init__(self, message, **kwargs):
        error.PrewikkaUserError.__init__(self, message=message, **kwargs)


class DatabaseSchemaError(DatabaseError):
    name = N_("Database schema error")



# Internal workaround since SWIG generated exception use class RuntimeError
def _fix_exception(func):
        def inner(self, *args, **kwargs):
            try:
                ret = func(self, *args, **kwargs)
            except RuntimeError as e:
                raise DatabaseError(message=text_type(e))

            return ret
        return inner


def _use_flock(func):

    def inner(self, *args, **kwargs):
        fd = open(__file__, 'r')

        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            ret = func(self, *args, **kwargs)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)

        return ret

    return inner


def use_transaction(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if env.db._transaction_state:
            return func(self, *args, **kwargs)

        env.db.transaction_start()
        try:
            ret = func(self, *args, **kwargs)
        except:
            env.db.transaction_abort()
            raise

        env.db.transaction_end()
        return ret

    return inner


def use_lock(table):
    def real_decorator(func):

        @use_transaction
        def inner(self, *args, **kwargs):
            env.db._lock_table(table)

            try:
                ret = func(self, *args, **kwargs)
            except:
                env.db._unlock_table(table)
                raise

            env.db._unlock_table(table)
            return ret

        return inner

    return real_decorator


class SQLScript(object):
    """This is the main class describing an SQL script (install / update / branch migration)

    ::type:: Describe the kind of database script : "branch", "update", "install"
    ::version:: Version the database is going to use after successful insertion of the script
    ::branch:: Optional name of the branch this script apply to
    ::from_branch:: Optional, the script only apply if the current (branch, version) is the one specified

    type = "branch" from_branch=("branch", "version") branch="B" version="target"
    type = "update" version="target" optional=[branch]
    type = "install" version="target" optional=[branch]

    """

    __metaclass__ = abc.ABCMeta
    __all__ = [ "type", "branch", "version", "from_branch" ]

    type = "update"
    branch = None
    version = None
    from_branch = None

    def __init__(self, dbup):
        self.db = dbup
        self.query_logs = []
        self._module_name = dbup._module_name
        self._full_module_name = dbup._full_module_name
        self._query_filter = { "sqlite3": self._mysql2sqlite, "pgsql": self._mysql2pgsql, "mysql": self._mysqlhandler }[self.db.getType()]

        if self.type in ("install", "update"):
           if not self.version:
                raise Exception("SQL %s script require 'version' attribute" % self.type)

        elif self.type == "branch":
            if not all(getattr(self, i) for i in ("from_branch", "branch", "version")):
                raise Exception("SQL branch script require 'from_branch', 'branch', and 'version' attribute")

    @staticmethod
    def _sub(_stbl, input):
        for i in _stbl:
            input = re.sub(i[0], i[1], input)

        return input

    def _mysql2pgsql(self, input):
        _stbl = [ ("#.*", ""),
                  (" INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT", " SERIAL PRIMARY KEY"),
                  ("BIGINT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT", "BIGSERIAL PRIMARY KEY"),
                  ("BLOB", "BYTEA"),
                  (" TINYINT UNSIGNED ", " INT4 "),
                  (" TINYINT ", " INT2 "),
                  (" SMALLINT UNSIGNED ", " INT8 "),
                  (" SMALLINT ", " INT4 "),
                  (" BIGINT UNSIGNED ", " INT8 "),
                  (" BIGINT ", " INT8 "),
                  (" INT(EGER)? UNSIGNED ", " INT8 "),
                  (" INT(EGER)? ", " INT4 "),
                  ("DATETIME", "TIMESTAMP"),
                  ("ENGINE=InnoDB", ""),
                  ("\"([^\"]*)\"", "'\\1'"),
                  ("\"\([^\"]*\)\"", "'\1'"),
                  ("(\S*) ENUM\((.*)\)", "\\1 TEXT CHECK (\\1 IN (\\2))"),
                  ("VARCHAR[ ]*[^)]+\)", "TEXT"),
                  ("(DROP INDEX [^ ]*) ON [^;]*", "\\1")]

        return self._sub(_stbl, input)

    def _mysql2sqlite(self, input):
        _stbl = [ ("#.*", ""),
                  ("[a-zA-Z]*INT ", "INTEGER "),
                  ("UNSIGNED ", ""),
                  ("ENUM[ ]*[^)]+\)", "TEXT"),
                  ("VARCHAR[ ]*[^)]+\)", "TEXT"),
                  ("AUTO_INCREMENT", "AUTOINCREMENT"),
                  ("ENGINE=InnoDB", ""),
                  ("ALTER TABLE [^ ]* DROP.*", ""),
                  ("(DROP INDEX [^ ]*) ON [^;]*", "\\1")]

        return self._sub(_stbl, input)

    def _mysqlhandler(self, input):
        return input

    def query(self, input):
        for q in self._query_filter(input).split(";"):
            q = q.strip()
            if q:
                self.query_logs.append(q);
                self.db.query(q)

    @abc.abstractmethod
    def run(self):
        pass

    @use_transaction
    def apply(self):
        log.getLogger().info("%s: please standby while %s is applied", self._full_module_name, text_type(self))

        self.run()

        if self.type == "install":
            env.db.upsert("Prewikka_Module_Registry", ("module", "branch", "version"), ((self._full_module_name, self.branch, self.version),), pkey=("module",))

        elif self.type == "update":
            self.db.query("UPDATE Prewikka_Module_Registry SET version=%s WHERE module=%s%s" % (self.db.escape(self.version), self.db.escape(self._full_module_name), self.db._chknull("branch", self.branch)))

        elif self.type == "branch":
            self.db.query("UPDATE Prewikka_Module_Registry SET branch=%s, version=%s, enabled=1 WHERE module=%s",
                          self.branch, self.version, self._full_module_name)

        self.db._update_state(self.version, self.branch)

    def get_version_string(self):
        if not self.branch:
            return self.version
        else:
            return "%s[%s]" % (self.branch, self.version)

    def __str__(self):
        return "%s:%s" % (self.type, self.get_version_string())

    def __eq__(self, other):
        return all(getattr(self, i) == getattr(other, i) for i in self.__all__)


class DatabaseHelper(object):
    def __getattr__(self, x):
        return self.__dict__.get(x, getattr(env.db, x))



class DatabaseUpdateHelper(DatabaseHelper):
    _default_modinfo = ModuleInfo(None, None, True)

    def _init_version_attr(self):
        if self._initialized:
            return

        module = self.modinfos.get(self._full_module_name, self._default_modinfo)

        self._from_branch = module.branch
        self._from_version = module.version
        self._need_enable = not(module.enabled)
        self._initialized = True

    def __init__(self, module_name, reqversion, reqbranch=None):
        DatabaseHelper.__init__(self) #for use_transaction

        self._reqbranch = reqbranch
        self._reqversion = reqversion
        self._module_name = module_name.split(":")[0]
        self._full_module_name = module_name
        self._initialized = False

    def check(self):
        self._init_version_attr()

        if not self._from_version and self._reqversion:
            raise DatabaseSchemaError(N_("database installation required"))

        if self._need_enable:
            raise DatabaseSchemaError(N_("database activation required"))

        if self._reqbranch and self._from_branch != self._reqbranch:
            raise DatabaseSchemaError(N_("database schema branch %(required)s required (found %(current)s)",
                                         {'required': self._reqbranch, 'current': self._from_branch}))

        if self._reqversion and self._from_version != self._reqversion:
            raise DatabaseSchemaError(N_("database schema version %(required)s required (found %(current)s)",
                                         {'required': self._get_version_string(self._reqbranch, self._reqversion),
                                          'current': self._get_version_string(self._from_branch, self._from_version)}))

    def _update_state(self, version, branch):
        self._from_branch = branch
        self._from_version = version

    def _get_update_directories(self):
        for i in pkg_resources.iter_entry_points("prewikka.updatedb", self._module_name):
            try:
                yield i.load().__path__[0]
            except Exception as e:
                log.getLogger().exception("[%s]: error loading SQL updates: %s", self._full_module_name, e)

    def _get_schema_list(self, **kwargs):
        from_version = to_version = None

        if "from_version" in kwargs:
            from_version = pkg_resources.parse_version(kwargs.pop("from_version"))

        if "to_version" in kwargs:
            to_version = pkg_resources.parse_version(kwargs.pop("to_version"))

        dirnames = self._get_update_directories()

        for importer, package_name, _ in pkgutil.iter_modules(dirnames):
            try:
                mod = importer.find_module(package_name).load_module(package_name).SQLUpdate(self)
            except Exception as e:
                log.getLogger().exception("[%s]: error loading SQL update '%s' : %s" % (self._full_module_name, package_name, e))
                continue

            if any(kwargs[k] != getattr(mod, k) for k in kwargs.keys()):
                continue

            version = pkg_resources.parse_version(mod.version)
            if (not from_version or (version >= from_version)) and (not to_version or (version <= to_version)):
                    yield mod


    def _resolve_branch_switch(self, curbranch, curversion, outstack=[]):

        for upd in self._list(from_branch=(curbranch, curversion), type="branch"):
            if upd.branch == self._reqbranch and pkg_resources.parse_version(upd.version) <= pkg_resources.parse_version(self._reqversion):
                return outstack + [upd]

            elif upd in outstack:
                log.getLogger().warning("cyclic branch dependencies detected: %s",  " -> ".join(text_type(i) for i in outstack + [upd]))
                continue

            else:
                ret = self._resolve_branch_switch(upd.branch, upd.version, outstack=outstack[:] + [upd])
                if ret:
                    return ret

        return []

    def _list(self, *args, **kwargs):
        fv = self._get_schema_list(*args, **kwargs)
        return sorted(fv, key=operator.attrgetter("version"))

    def _get_install_schema(self):
        ret = self._list(to_version=self._reqversion, branch=self._reqbranch, type="install")
        if not ret:
            raise error.PrewikkaUserError(N_("Database installation error"),
                                          N_("No database installation script found for module %(module)s, version %(version)s",
                                             {'module': self._full_module_name, 'version': self._get_version_string(self._reqbranch, self._reqversion)}))

        return ret[-1]

    def _get_branch_update(self):
        prev = self._resolve_branch_switch(self._from_branch, self._from_version)
        if not prev:
            raise error.PrewikkaUserError(
                N_("Database migration error"),
                N_("No database branch migration script found for module %(module)s, branch transition %(current)s -> %(required)s",
                    {'module': self._full_module_name,
                     'current': self._get_version_string(self._from_branch, self._from_version),
                     'required': self._get_version_string(self._reqbranch, "<=" + self._reqversion)})
            )

        return prev

    @staticmethod
    def _get_version_string(branch, version):
        if not branch:
            return version
        else:
            return "%s[%s]" % (branch, version)

    def list(self):
        if not self._reqversion:
            return []

        self._init_version_attr()
        from_version, prev = self._from_version, []

        if not from_version:
            prev = [ self._get_install_schema() ]

        elif self._from_branch != self._reqbranch:
            prev = self._get_branch_update()

        if prev:
            from_version = prev[-1].version

        if from_version == self._reqversion:
            return prev

        ret = self._list(from_version=from_version, to_version=self._reqversion, branch=self._reqbranch, type="update")
        if not(ret) or ret[-1].version != self._reqversion:
            raise error.PrewikkaUserError(
                N_("Database migration error"),
                N_("No linear migration script found for module %(module)s %(version1)s -> %(version2)s",
                    {'module': self._full_module_name,
                     'version1': self._get_version_string(self._from_branch, self._from_version),
                     'version2': self._get_version_string(self._reqbranch, self._reqversion)})
            )

        return prev + ret

    @use_transaction
    def _apply(self):
        [ update.apply() for update in self.list() ]
        self.check()

    @_use_flock
    def apply(self):
        # We call _init_version_attr() outside the transaction because it fails
        # when the tables do not exist (eg. during database initialization)
        # and we don't want the whole transaction to be rolled back.
        self._init_version_attr()
        self._apply()

    def get_schema_version(self):
        self._init_version_attr()
        return self._from_version


class DatabaseCommon(preludedb.SQL):
    required_branch = version.__branch__
    required_version = "0"

    NotNone = NotNone
    __sentinel = object()
    __ALL_PROPERTIES = object()

    __TRANSACTION_STATE_NONE  = 0
    __TRANSACTION_STATE_BEGIN = 1
    __TRANSACTION_STATE_QUERY = 2

    @cache.memoize_property("modinfos_cache")
    def modinfos(self):
        try:
            rows = self.query("SELECT module, branch, version, enabled FROM Prewikka_Module_Registry")
        except:
            return {}

        return dict((i[0], ModuleInfo(i[1], i[2], int(i[3]))) for i in rows)

    def _prefilter_iterate(self, l):
        tmp = []
        for v in l:
            tmp.append(text_type(self.escape(v)))

        if self.__ESCAPE_PREFILTER.get(type(v)) == self._prefilter_iterate:
            fmt = '%s'
        else:
            fmt = '(%s)'

        return fmt % ', '.join(tmp)

    @_fix_exception
    def __init__(self, config):
        env.db = self

        self.__ESCAPE_PREFILTER = {
                datetime: lambda dt: self.escape(self.datetime(dt)),
                set: self._prefilter_iterate,
                list: self._prefilter_iterate,
                tuple: self._prefilter_iterate,
                types.GeneratorType: self._prefilter_iterate
        }

        self._transaction_state = self.__TRANSACTION_STATE_NONE

        settings = { "host": "localhost", "name": "prewikka", "user": "prewikka", "type": "mysql" }
        stpl = tuple((k, v) for k, v in config.items())
        settings.update(stpl)

        preludedb.SQL.__init__(self, settings)

        self._version = self.getServerVersion()
        self._dbhash = hash(stpl)
        self._dbtype = settings["type"]

        dh = DatabaseUpdateHelper("prewikka", self.required_version, self.required_branch)
        dh.apply()

        self._last_plugin_activation_change = self._get_last_plugin_changed()

    @staticmethod
    def parse_datetime(date):
        if "." in date:
            fmt = "%Y-%m-%d %H:%M:%S.%f"
        else:
            fmt = "%Y-%m-%d %H:%M:%S"

        return datetime.strptime(date, fmt).replace(tzinfo=utils.timeutil.timezone("UTC"))

    @staticmethod
    def datetime(t):
        if t is None:
            return None

        if isinstance(t, datetime):
            # Only timezone-aware datetimes are accepted
            return t.astimezone(utils.timeutil.timezone("UTC")).strftime("%Y-%m-%d %H:%M:%S.%f")
        else:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))

    def kwargs2query(self, kwargs, prefix=""):
        if not kwargs:
            return ""

        qs = []
        for field, val in kwargs.items():
            if not val:
                qs.append("%s IS NULL" % (field))

            elif val is NotNone:
                qs.append("%s IS NOT NULL" % (field))

            else:
                op = "="
                if isinstance(val, (list, tuple)):
                    op = "IN"

                elif isinstance(val, bool):
                    val = int(val)

                qs.append("%s %s %s" % (field, op, self.escape(val)))

        return prefix + " AND ".join(qs)

    def query(self, sql, *args, **kwargs):
        if self._transaction_state == self.__TRANSACTION_STATE_BEGIN:
            self.transactionStart()
            self._transaction_state = self.__TRANSACTION_STATE_QUERY

        if args:
            sql = sql % tuple(self.escape(value) for value in args)
        elif kwargs:
            sql = sql % dict((key, self.escape(value)) for key, value in kwargs.items())

        return preludedb.SQL.query(self, sql)

    def _chk(self, key, value, join="AND"):
        if value is not None and value is not self.__ALL_PROPERTIES:
            return " %s %s = %s" % (join, key, self.escape(value))

        return ""

    def _chknull(self, key, value, join="AND"):
        if value is None:
            return " %s %s IS NULL" % (join, key)
        else:
            return self._chk(key, value, join=join)

    @staticmethod
    def _mklist(value):
        if isinstance(value, (list, tuple)):
            return value
        else:
            return (value,)

    def getType(self):
        return self._dbtype

    def escape(self, data):
        prefilter = self.__ESCAPE_PREFILTER.get(type(data))
        if prefilter:
            return prefilter(data)

        if not isinstance(data, compat.STRING_TYPES):
            return data if data is not None else "NULL"

        return preludedb.SQL.escape(self, data)

    def is_plugin_active(self, plugin):
        plugin = self.modinfos.get(plugin)
        if plugin:
            return plugin.enabled == 1

        return True

    def _get_last_plugin_changed(self):
        rows = self.query("SELECT time FROM Prewikka_Module_Changed")[0][0]
        return utils.timeutil.get_timestamp_from_string(rows)

    def has_plugin_changed(self):
        last = self._get_last_plugin_changed()

        if last <= self._last_plugin_activation_change:
            return False

        self._last_plugin_activation_change = last
        self.modinfos_cache.clear()

        return True

    def trigger_plugin_change(self):
        self.query("UPDATE Prewikka_Module_Changed SET time=current_timestamp")

    def _get_merge_value(self, merged, field, rownum):
        value = merged[field]
        if not isinstance(value, (tuple, list)):
            return value

        if rownum >= len(value):
            raise Exception("merge value should be unique, or list with the same number of rows")

        return value[rownum]

    def _upsert_prepare_row(self, table, fields, row):
        return text_type(self.escape(row))

    def _upsert_prepare(self, table, pkey, fields, values_rows, returning=[], merge={}, func=None):
        up = []
        if func:
            up = ["%s=%s" % (f, func(f)) for f in fields]

        merged = {} if isinstance(merge, int) else merge

        vl = []
        delq = []

        for idx, row in enumerate(values_rows):
            vl.append(self._upsert_prepare_row(table, fields, row))

            if not merge:
                continue

            tmpl1 = []
            tmpl2 = []
            for field, value in zip(fields, row):
                if field in merged:
                    tmpl1.append("%s = %s" % (field, self.escape(self._get_merge_value(merged, field, idx))))

                elif field in pkey:
                    tmpl2.append("%s = %s" % (field, self.escape(value)))

            delq.append(" AND ".join([" AND ".join(tmpl1), "NOT(" + " AND ".join(tmpl2) + ")"]))

        if not vl:
            delq.append(" AND ".join("%s = %s" % (f, self.escape(v)) for f, v in merged.items()))

        return ", ".join(fields), ", ".join(vl), ", ".join(up), ", ".join(returning), " AND ".join(delq)

    def _unlock_table(self, table):
        pass

    def transaction_start(self):
        # The actual transaction will be started on the first query
        self._transaction_state = self.__TRANSACTION_STATE_BEGIN

    def transaction_end(self):
        if self._transaction_state == self.__TRANSACTION_STATE_QUERY:
            self.transactionEnd()

        self._transaction_state = self.__TRANSACTION_STATE_NONE

    def transaction_abort(self):
        if self._transaction_state == self.__TRANSACTION_STATE_QUERY:
            self.transactionAbort()

        self._transaction_state = self.__TRANSACTION_STATE_NONE

    def __hash__(self):
        return self._dbhash


class MySQLDatabase(DatabaseCommon):
    def _lock_table(self, table):
        self.query("LOCK TABLES %s" % ", ".join(t + " WRITE" for t in self._mklist(table)))

    def _unlock_table(self, table):
        self.query("UNLOCK TABLES;")

    def _mysql_upsert(self, table, pkey, fields, values_rows, returning=[], merge={}):
        if returning:
            values_rows = list(values_rows)

        fieldfmt, vlfmt, upfmt, retfmt, delfmt = self._upsert_prepare(table, pkey, fields, values_rows, returning, merge, lambda x: "VALUES(%s)" % x)

        if vlfmt:
            self.query("INSERT INTO %s (%s) VALUES %s ON DUPLICATE KEY UPDATE %s" % (table, fieldfmt, vlfmt, upfmt))

        if delfmt:
            self.query("DELETE FROM %s WHERE %s" % (table, delfmt))

        if retfmt:
            wh = []
            for row in values_rows:
                vl = " AND ".join([ "%s = %s" % (field, self.escape(row[i])) for i, field in enumerate(pkey) ])
                wh.append("(%s)" % (vl))

            return self.query("SELECT %s FROM %s WHERE %s" % (retfmt, table, " OR ".join(wh)))

    @use_transaction
    def upsert(self, table, fields, values_rows, pkey=[], returning=[], merge={}):
        if not pkey:
            pkey = fields

        return self._mysql_upsert(table, pkey, fields, values_rows, returning, merge)


class PgSQLDatabase(DatabaseCommon):
    def __init__(self, *args, **kwargs):
        DatabaseCommon.__init__(self, *args, **kwargs)

    def _lock_table(self, table):
        self.query("LOCK TABLE %s IN EXCLUSIVE MODE" % ", ".join(self._mklist(table)))

    @cache.memoize("table_info")
    def _get_table_info(self, table):
        out = {}
        typemap = {"bigint": "integer", "smallint": "integer", "character varying": "text"}

        for field, _type, defval in env.db.query("SELECT column_name, data_type, column_default FROM information_schema.columns WHERE table_name = %s", table.lower()):
            out[field] = utils.AttrObj(type=_type, generic_type=typemap.get(_type, _type), default=defval, auto_increment="nextval" in (defval or ""))

        return out

    def _upsert_prepare_row(self, table, fields, row):
        out = []
        dtype = self._get_table_info(table)

        for f, v in zip(fields, row):
            cast = ""

            if self._version >= 90500 and dtype[f].auto_increment and v is None:
                v = "DEFAULT"
            else:
                if dtype[f].generic_type != "text":
                    cast = "::%s" % dtype[f].type

                v = text_type(self.escape(v)) + cast

            out.append(v)

        return "(" + text_type(", ".join(out)) + ")"

    def _pgsql_upsert_cte_query(self, table, pkey, upfmt, fields, fieldfmt, vlfmt, retfmt):
        up_pkfmt = []
        in_pkfmt = []
        for v in pkey:
            up_pkfmt.append("%s.%s = nv.%s" % (table, v, v))
            in_pkfmt.append("updated.%s = nv.%s" % (v, v))

        dtype = self._get_table_info(table)
        insfmt = ", ".join(filter(lambda x: not(dtype[x].auto_increment), fields))

        update = "UPDATE %s SET %s FROM nv WHERE %s RETURNING %s.*" % (table, upfmt, " AND ".join(up_pkfmt), table)
        insert = "INSERT INTO %s (%s) SELECT %s FROM nv WHERE NOT EXISTS (SELECT 1 FROM updated WHERE %s)" % (table, insfmt, insfmt, " AND ".join(in_pkfmt))
        if retfmt:
            insert = "%s RETURNING %s" % (insert, retfmt)

        query = "WITH nv (%s) AS (VALUES %s), updated AS (%s)" % (fieldfmt, vlfmt, update)
        if retfmt:
            query = "%s, inserted AS (%s) SELECT %s FROM inserted UNION ALL SELECT %s FROM updated" % (query, insert, retfmt, retfmt)
        else:
            query = " ".join((query, insert))

        return self.query(query)

    def _pgsql_upsert_cte(self, table, pkey, fields, values_rows, returning=[], merge={}):
        fieldfmt, vlfmt, upfmt, retfmt, delfmt = self._upsert_prepare(table, pkey, fields, values_rows, returning, merge, lambda x: "nv.%s" % x)

        self._lock_table(table)
        try:
            if vlfmt:
                ret = self._pgsql_upsert_cte_query(table, pkey, upfmt, fields, fieldfmt, vlfmt, retfmt)

            if delfmt:
                self.query("DELETE FROM %s WHERE %s" % (table, delfmt))
        finally:
            self._unlock_table(table)

        if vlfmt and retfmt:
            return ret

    def _pgsql_upsert(self, table, pkey, fields, values_rows, returning=[], merge={}):
        fieldfmt, vlfmt, upfmt, retfmt, delfmt = self._upsert_prepare(table, pkey, fields, values_rows, returning, merge, lambda x: "EXCLUDED.%s" % (x))
        if vlfmt:
            if retfmt:
                retfmt = " RETURNING %s" % retfmt

            ret = self.query("INSERT INTO %s (%s) VALUES %s ON CONFLICT (%s) DO UPDATE SET %s%s" % (table, fieldfmt, vlfmt, ",".join(pkey), upfmt, retfmt))

        if delfmt:
            self.query("DELETE FROM %s WHERE %s" % (table, delfmt))

        if vlfmt and retfmt:
            return ret

    def _pgsql_upsert_emulate_single(self, table, pkey, fields, row, fieldfmt, retfmt):
        up_fmt = []
        wh_fmt = []
        vl_fmt = []

        for i, v in enumerate(fields):
            if v in pkey:
                wh_fmt.append("%s = %s" % (v, self.escape(row[i])))

            up_fmt.append("%s = %s" % (v, self.escape(row[i])))
            vl_fmt.append(text_type(self.escape(row[i])))

        ret = self.query("UPDATE %s SET %s WHERE %s%s" % (table, ", ".join(up_fmt), " AND ".join(wh_fmt), retfmt))
        if ret:
            return ret

        return self.query("INSERT INTO %s (%s) SELECT %s WHERE NOT EXISTS (SELECT 1 FROM %s WHERE %s)%s" %
                          (table, fieldfmt, ", ".join(vl_fmt), table, " AND ".join(wh_fmt), retfmt))

    def _pgsql_upsert_emulate(self, table, pkey, fields, values_rows, returning=[], merge={}):
        values_rows = list(values_rows)

        fieldfmt, _, _, retfmt, delfmt = self._upsert_prepare(table, pkey, fields, values_rows, returning, merge)
        if retfmt:
            retfmt = " RETURNING %s" % retfmt

        returning = []
        self._lock_table(table)

        try:
            for row in values_rows:
                ret = self._pgsql_upsert_emulate_single(table, pkey, fields, row, fieldfmt, retfmt)
                if ret and retfmt:
                    returning.append(ret[0])

            if delfmt:
                self.query("DELETE FROM %s WHERE %s" % (table, delfmt))

        finally:
            self._unlock_table(table)

        return returning

    @use_transaction
    def upsert(self, table, fields, values_rows, pkey=[], returning=[], merge={}):
        if not pkey:
            pkey = fields

        if self._version >= 90500:
            ret = self._pgsql_upsert(table, pkey, fields, values_rows, returning, merge)

        elif self._version >= 90100:
            ret = self._pgsql_upsert_cte(table, pkey, fields, values_rows, returning, merge)

        else:
            ret = self._pgsql_upsert_emulate(table, pkey, fields, values_rows, returning, merge)

        return ret


class NoDatabase(DatabaseCommon):
    def __init__(self, *args, **kwargs):
        DatabaseCommon.__init__(self, *args, **kwargs)

    def query(self, *args, **kwargs):
        raise error.PrewikkaUserError(N_("Database configuration error"), N_("Only MySQL and PostgreSQL databases are supported at the moment"))


class Database(object):
    def __new__(cls, config):
        type = config.get("type")
        if type == "pgsql":
            return PgSQLDatabase(config)

        elif type == "mysql":
            return MySQLDatabase(config)

        else:
            return NoDatabase(config)
