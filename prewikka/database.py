# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
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

import time, abc, fcntl
import re, operator, pkg_resources, pkgutil, glob, os.path, sys
from datetime import datetime

import preludedb
from prewikka import log, error, utils, version, env, compat


class DatabaseSchemaError(error.PrewikkaUserError):
    def __init__(self, err):
        error.PrewikkaUserError.__init__(self, _("Database schema error"), err)


__flock_fd = open(__file__, 'r')


def use_flock(func):
    def inner(self, *args, **kwargs):
        fcntl.flock(__flock_fd, fcntl.LOCK_EX)

        try:
            ret = func(self, *args, **kwargs)
        finally:
            fcntl.flock(__flock_fd, fcntl.LOCK_UN)

        return ret

    return inner


def use_transaction(func):
    def inner(self, *args, **kwargs):
        self.transactionStart()
        try:
            ret = func(self, *args, **kwargs)
        except:
            self.transactionAbort()
            raise
        self.transactionEnd()
        return ret
    return inner


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
        self._module_name = dbup._module_name
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
                  (" BIGINT UNSIGNED ", " NUMERIC(20) "),
                  (" BIGINT ", " INT8 "),
                  (" INT(EGER)? UNSIGNED ", " INT8 "),
                  (" INT(EGER)? ", " INT4 "),
                  ("DATETIME", "TIMESTAMP"),
                  ("ENGINE=InnoDB", ""),
                  ("\"([^\"]*)\"", "'\\1'"),
                  ("\"\([^\"]*\)\"", "'\1'"),
                  ("(\S*) ENUM\((.*)\)", "\\1 TEXT CHECK (\\1 IN (\\2))"),
                  ("VARCHAR[ ]*[^)]+\)", "TEXT") ]

        return self._sub(_stbl, input)

    def _mysql2sqlite(self, input):
        _stbl = [ ("#.*", ""),
                  ("DROP .*", ""),
                  ("[a-zA-Z]*INT ", "INTEGER "),
                  ("UNSIGNED ", ""),
                  ("ENUM[ ]*[^)]+\)", "TEXT"),
                  ("VARCHAR[ ]*[^)]+\)", "TEXT"),
                  ("AUTO_INCREMENT", "AUTOINCREMENT"),
                  ("ENGINE=InnoDB", "") ]

        return self._sub(_stbl, input)

    def _mysqlhandler(self, input):
        return input

    def query(self, input):
        for q in self._query_filter(input).split(";"):
            q = q.strip()
            if q:
                self.db.query(q)

    @abc.abstractmethod
    def run(self):
        pass

    def __metadata_upsert(self):
        # Update or insert metadata for the module as necessary,
        # depending on whether the plugin already existed without a schema
        # or not.
        module = self.db.escape(self._module_name)
        if self.db.query('SELECT 1 FROM Prewikka_Module_Registry WHERE module = %s' % module):
            self.db.query('UPDATE Prewikka_Module_Registry SET branch = %s, version = %s WHERE module = %s' %
                  (self.db.escape(self.branch), self.db.escape(self.version), module))
        else:
            self.db.query('INSERT INTO Prewikka_Module_Registry(module, branch, version, enabled) VALUES(%s, %s, %s, 1)' %
                  (module, self.db.escape(self.branch), self.db.escape(self.version)))

    def __apply(self):
        self.run()

        if self.type == "install":
            self.__metadata_upsert()

        elif self.type == "update":
            self.db.query("UPDATE Prewikka_Module_Registry SET version=%s WHERE module=%s%s" % (self.db.escape(self.version), self.db.escape(self._module_name), self.db._chknull("branch", self.branch)))

        elif self.type == "branch":
            self.db.query("UPDATE Prewikka_Module_Registry SET branch=%s, version=%s, enabled=1 WHERE module=%s" % (
                          self.db.escape(self.branch), self.db.escape(self.version), self.db.escape(self._module_name)))

        self.db._update_state(self.version, self.branch)

    def apply(self, transaction=True):
        log.getLogger().info("%s: please standby while %s is applied", self._module_name, str(self))

        if not transaction:
            return self.__apply()

        else:
            self.db.transactionStart()
            try:
                self.__apply()
            except Exception as e:
                self.db.transactionAbort()
                raise e

            self.db.transactionEnd()

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
    def _get_database_version(self):
        try:
                infos = self.query("SELECT branch, version, enabled FROM Prewikka_Module_Registry WHERE module = %s" % self.escape(self._module_name))
                branch, version, enabled = infos[0]
        except Exception as e:
                return None, None, False

        return branch, version, not(bool(int(enabled)))

    def _init_version_attr(self):
        if not self._initialized:
            self._from_branch, self._from_version, self._need_enable = self._get_database_version()
            self._initialized = True

    def __init__(self, module_name, reqversion, reqbranch=None):
        DatabaseHelper.__init__(self) #for use_transaction

        self._reqbranch = reqbranch
        self._reqversion = reqversion
        self._module_name = module_name
        self._initialized = False

    def check(self):
        self._init_version_attr()

        if not self._from_version and self._reqversion:
            raise DatabaseSchemaError(_("database installation required"))

        if self._need_enable:
            raise DatabaseSchemaError(_("database activation required"))

        if self._reqbranch and self._from_branch != self._reqbranch:
            raise DatabaseSchemaError("database schema branch %s required (found %s)" % (self._reqbranch, self._from_branch))

        if self._reqversion and self._from_version != self._reqversion:
            raise DatabaseSchemaError("database schema version %s required (found %s)" % (self._get_version_string(self._reqbranch, self._reqversion), self._get_version_string(self._from_branch, self._from_version)))

    def _update_state(self, version, branch):
        self._from_branch = branch
        self._from_version = version

    def _get_update_directories(self):
        for i in pkg_resources.iter_entry_points("prewikka.updatedb", self._module_name):
            try:
                yield i.load().__path__[0]
            except Exception as e:
                log.getLogger().exception("[%s]: error loading SQL updates: %s", self._module_name, e)

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
                log.getLogger().exception("[%s]: error loading SQL update '%s' : %s" % (self._module_name, package_name, e))
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
                log.getLogger().warning("cyclic branch dependencies detected: %s",  " -> ".join(str(i) for i in outstack + [upd]))
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
            raise error.PrewikkaUserError(_("Database installation error"), _("No database installation script found for module %(module)s, version %(version)s") % {'module': self._module_name, 'version': self._get_version_string(self._reqbranch, self._reqversion)})

        return ret[-1]

    def _get_branch_update(self):
        prev = self._resolve_branch_switch(self._from_branch, self._from_version)
        if not prev:
            raise error.PrewikkaUserError(_("Database migration error"), "No database branch migration script found for module %s, branch transition %s -> %s" % (self._module_name, self._get_version_string(self._from_branch, self._from_version), self._get_version_string(self._reqbranch, "<=" + self._reqversion)))

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
            raise error.PrewikkaUserError(_("Database migration error"), _("No linear migration script found for module %(module)s %(version1)s -> %(version2)s") % {
                'module': self._module_name,
                'version1': self._get_version_string(self._from_branch, self._from_version),
                'version2': self._get_version_string(self._reqbranch, self._reqversion)
            })

        return prev + ret

    @use_transaction
    def _apply(self):
        [ update.apply(transaction=False) for update in self.list() ]
        self.check()

    @use_flock
    def apply(self):
        # We call _init_version_attr() outside the transaction because it fails
        # when the tables do not exist (eg. during database initialization)
        # and we don't want the whole transaction to be rolled back.
        self._init_version_attr()
        self._apply()

    def get_schema_version(self):
        self._init_version_attr()
        return self._from_version


class Database(preludedb.SQL):
    required_branch = version.__branch__
    required_version = "0"

    __sentinel = object()
    __ALL_PROPERTIES = object()

    def __init__(self, config):
        env.db = self

        settings = { "host": "localhost", "name": "prewikka", "user": "prewikka", "type": "mysql" }
        settings.update([(k, str(v)) for k, v in config.items()])

        preludedb.SQL.__init__(self, settings)
        self._dbtype = settings["type"]

        dh = DatabaseUpdateHelper("prewikka", self.required_version, self.required_branch)
        dh.apply()

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

    @staticmethod
    def parse_datetime(date):
        return datetime.strptime(date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=utils.timeutil.timezone("UTC"))

    def escape(self, data):
        if not isinstance(data, compat.STRING_TYPES):
            return data if data is not None else "NULL"

        return preludedb.SQL.escape(self, data)

    @staticmethod
    def datetime(t):
        if t is None:
            return "NULL"

        return "'" + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)) + "'"

    def is_plugin_active(self, plugin):
        r = self.query("SELECT enabled FROM Prewikka_Module_Registry WHERE module = %s" % (self.escape(plugin)))
        if r:
            return int(r[0][0]) == 1

        return True

    def get_last_plugin_activation_change(self):
        d = self.query("SELECT time FROM Prewikka_Module_Changed")[0][0]
        return utils.timeutil.get_timestamp_from_string(d)

    def trigger_plugin_change(self):
        self.query("UPDATE Prewikka_Module_Changed SET time=current_timestamp")

    def get_property_fail(self, user, key, view=None, default=__sentinel):
        config = {}

        rows = self.query("SELECT view, name, value FROM Prewikka_User_Configuration WHERE userid = %s%s%s" % (self.escape(user.id), self._chknull("view", view), self._chk("name", key)))
        for vname, name, val in rows:
            viewd = config.setdefault(vname, {})

            if not name in viewd:
                viewd[name] = val
            else:
                if not isinstance(viewd[name], list):
                    viewd[name] = [ viewd[name] ]

                viewd[name].append(val)

        if view is self.__ALL_PROPERTIES:
            return config

        view = config.get(view, {})
        return view.get(key, default) if default is not self.__sentinel else view[key]

    def get_properties(self, user):
        return self.get_property_fail(user, None, view=self.__ALL_PROPERTIES)

    def get_property(self, user, key, view=None, default=None):
        return self.get_property_fail(user, key, view, default)

    @use_transaction
    def set_property(self, user, key, value, view=None):
        self.del_property(user, key, view)

        view, userid, key = self.escape(view), self.escape(user.id), self.escape(key)
        for val in self._mklist(value):
            self.query("INSERT INTO Prewikka_User_Configuration (view, userid, name, value) VALUES (%s,%s,%s,%s)" % (view, userid, key, self.escape(val)))

    def has_property(self, user, key):
        return bool(self.query("SELECT value FROM Prewikka_User_Configuration WHERE userid = %s AND name = %s AND value IS NOT NULL" % (self.escape(user.id), self.escape(key))))

    def del_property(self, user, key, view=None):
        self.query("DELETE FROM Prewikka_User_Configuration WHERE userid = %s%s%s" %  (self.escape(user.id), self._chknull("view", view), self._chk("name", key)))

    def del_properties(self, user, view=__ALL_PROPERTIES):
        return self.del_property(user, None, view=view)
