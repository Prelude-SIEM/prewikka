# Copyright (C) 2004-2014 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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


import sys
import time
import calendar

import prelude, preludedb
from prewikka import Error, User, Filter, utils, siteconfig

class DatabaseError(Exception):
    pass


class _DatabaseInvalidError(DatabaseError):
    def __init__(self, resource):
        self._resource = resource

    def __str__(self):
        return "invalid %s '%s'" % (self.type, self._resource)



class DatabaseInvalidUserError(_DatabaseInvalidError):
    type = "user"



class DatabaseInvalidSessionError(_DatabaseInvalidError):
    type = "session"



class DatabaseInvalidFilterError(_DatabaseInvalidError):
    type = "filter"


class DatabaseSchemaError(Exception):
    pass


def get_timestamp(s):
    return s and calendar.timegm(time.strptime(s, "%Y-%m-%d %H:%M:%S")) or None



class Database(preludedb.SQL):
    required_version = "0.9.11"

    def __init__(self, env, config):
        self._env = env

        settings = {}
        for name, default in (("file", None),
                              ("host", "localhost"),
                              ("port", None),
                              ("name", "prewikka"),
                              ("user", "prewikka"),
                              ("pass", None),
                              ("type", "mysql"),
                              ("log", None)):
            value = config.get(name, default)
            if value:
                settings[name] = value

        preludedb.SQL.__init__(self, settings)

        # check if the database has been created
        try:
            version = self.query("SELECT version FROM Prewikka_Version")[0][0]
        except preludedb.PreludeDBError as e:
            raise DatabaseSchemaError(e)

        if version != self.required_version:
            d = { "version": version, "reqversion": self.required_version }
            raise DatabaseSchemaError(_("Database schema version %(version)s found when %(reqversion)s was required") % d)

        # We don't want to impose an SQL upgrade script for this specific change,
        # but this can be moved to an SQL script upon the next schema update.
        self.query("UPDATE Prewikka_User_Configuration SET value='n/a' WHERE (name='alert.assessment.impact.completion' OR name='alert.assessment.impact.severity') AND value='none'")

    def escape(self, data):
        if not isinstance(data, str):
            return data if data is not None else "NULL"

        return preludedb.SQL.escape(self, data)

    def datetime(self, t):
        if t is None:
            return "NULL"

        return "'" + utils.time_to_ymdhms(time.gmtime(t)) + "'"

    def hasUser(self, login):
        return bool(self.query("SELECT login FROM Prewikka_User WHERE login = %s" % self.escape(login)))

    def createUser(self, login, email=None):
        self.query("INSERT INTO Prewikka_User (login, email) VALUES (%s,%s)" % \
                   (self.escape(login), self.escape(email)))

    def deleteUser(self, login):
        login = self.escape(login)
        self.transactionStart()
        try:
            self.query("DELETE FROM Prewikka_User WHERE login = %s" % login)
            self.query("DELETE FROM Prewikka_Permission WHERE login = %s" % login)
            self.query("DELETE FROM Prewikka_Session WHERE login = %s" % login)

            rows = self.query("SELECT id FROM Prewikka_Filter WHERE login = %s" % login)
            if len(rows) > 0:
                lst = ", ".join([ id[0] for id in rows ])
                self.query("DELETE FROM Prewikka_Filter_Criterion WHERE Prewikka_Filter_Criterion.id IN (%s)" % lst)

            self.query("DELETE FROM Prewikka_Filter WHERE login = %s" % login)
        except:
            self.transactionAbort()
            raise

        self.transactionEnd()

    def getConfiguration(self, login):

        login = self.escape(login)
        rows = self.query("SELECT view, name, value FROM Prewikka_User_Configuration WHERE login = %s" % login)

        config = { }
        for view, name, value in rows:
            if not config.has_key(view):
                config[view] = { }

            if not config[view].has_key(name):
                config[view][name] = value
            else:
                if isinstance(config[view][name], str):
                    config[view][name] = [ config[view][name] ]

                config[view][name] = config[view][name] + [ value ]

        return config

    def getUserLogins(self):
        return map(lambda r: r[0], self.query("SELECT login FROM Prewikka_User"))

    def getUser(self, login):
        return User.User(self, login, self.getLanguage(login), self.getPermissions(login), self.getConfiguration(login))

    def setPassword(self, login, password):
        self.query("UPDATE Prewikka_User SET password=%s WHERE login = %s" % (self.escape(password), self.escape(login)))

    def getPassword(self, login):
        rows = self.query("SELECT login, password FROM Prewikka_User WHERE login = %s" % (self.escape(login)))
        if not rows or rows[0][0] != login:
            raise DatabaseInvalidUserError(login)

        return rows[0][1]

    def hasPassword(self, login):
        return bool(self.query("SELECT password FROM Prewikka_User WHERE login = %s AND password IS NOT NULL" % self.escape(login)))

    def setLanguage(self, login, lang):
        self.query("UPDATE Prewikka_User SET lang=%s WHERE login = %s" % (self.escape(lang), self.escape(login)))

    def getLanguage(self, login):
        rows = self.query("SELECT lang FROM Prewikka_User WHERE login = %s" % (self.escape(login)))
        if len(rows) > 0:
            return rows[0][0]

        return None

    def setPermissions(self, login, permissions):
        self.transaction_start()
        self.query("DELETE FROM Prewikka_Permission WHERE login = %s" % self.escape(login))
        for perm in permissions:
            self.query("INSERT INTO Prewikka_Permission VALUES (%s,%s)" % (self.escape(login), self.escape(perm)))
        self.transaction_end()

    def getPermissions(self, login):
        return map(lambda r: r[0], self.query("SELECT permission FROM Prewikka_Permission WHERE login = %s" % self.escape(login)))

    def createSession(self, sessionid, login, time):
        self.query("INSERT INTO Prewikka_Session VALUES(%s,%s,%s)" %
                   (self.escape(sessionid), self.escape(login), self.datetime(time)))

    def updateSession(self, sessionid, time):
        self.query("UPDATE Prewikka_Session SET time=%s WHERE sessionid=%s" % (self.datetime(time), self.escape(sessionid)))

    def getSession(self, sessionid):
        rows = self.query("SELECT login, time FROM Prewikka_Session WHERE sessionid = %s" % self.escape(sessionid))
        if not rows:
            raise DatabaseInvalidSessionError(sessionid)

        login, t = rows[0]
        return login, get_timestamp(t)

    def deleteSession(self, sessionid):
        self.query("DELETE FROM Prewikka_Session WHERE sessionid = %s" % self.escape(sessionid))

    def deleteExpiredSessions(self, time):
        self.query("DELETE FROM Prewikka_Session WHERE time < %s" % self.datetime(time))

    def getAlertFilterNames(self, login):
        return map(lambda r: r[0], self.query("SELECT name FROM Prewikka_Filter WHERE login = %s" % self.escape(login)))

    def setFilter(self, login, filter):
        if self.query("SELECT name FROM Prewikka_Filter WHERE login = %s AND name = %s" %
                      (self.escape(login), self.escape(filter.name))):
            self.deleteFilter(login, filter.name)

        self.transactionStart()
        self.query("INSERT INTO Prewikka_Filter (login, name, comment, formula) VALUES (%s, %s, %s, %s)" %
                   (self.escape(login), self.escape(filter.name), self.escape(filter.comment), self.escape(filter.formula)))
        id = int(self.query("SELECT MAX(id) FROM Prewikka_Filter")[0][0])
        for name, element in filter.elements.items():
            self.query("INSERT INTO Prewikka_Filter_Criterion (id, name, path, operator, value) VALUES (%d, %s, %s, %s, %s)" %
                       ((id, self.escape(name)) + tuple([ self.escape(e) for e in element ])))
        self.transactionEnd()

    def getAlertFilter(self, login, name):
        rows = self.query("SELECT id, comment, formula FROM Prewikka_Filter WHERE login = %s AND name = %s" %
                          (self.escape(login), self.escape(name)))
        if len(rows) == 0:
            return None

        id, comment, formula = rows[0]
        elements = { }
        for element_name, path, operator, value in \
                self.query("SELECT name, path, operator, value FROM Prewikka_Filter_Criterion WHERE id = %d" % int(id)):
            elements[element_name] = path, operator, value

        return Filter.Filter(name, comment, elements, formula)

    def deleteFilter(self, login, name):
        id = long(self.query("SELECT id FROM Prewikka_Filter WHERE login = %s AND name = %s" % (self.escape(login), self.escape(name)))[0][0])
        self.query("DELETE FROM Prewikka_Filter WHERE id = %d" % id)
        self.query("DELETE FROM Prewikka_Filter_Criterion WHERE id = %d" % id)


