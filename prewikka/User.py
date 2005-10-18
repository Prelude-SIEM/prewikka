# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


from prewikka import Error


PERM_IDMEF_VIEW = "IDMEF_VIEW"
PERM_IDMEF_ALTER = "IDMEF_ALTER"
PERM_USER_MANAGEMENT = "USER_MANAGEMENT"
PERM_COMMAND = "COMMAND"
PERM_INTRUSIVE_COMMAND = "INTRUSIVE_COMMAND"

ALL_PERMISSIONS = [ PERM_IDMEF_VIEW,
                    PERM_IDMEF_ALTER,
                    PERM_USER_MANAGEMENT,
                    PERM_COMMAND,
                    PERM_INTRUSIVE_COMMAND ]

ADMIN_LOGIN = "admin"

class PermissionDeniedError(Error.SimpleError):
    def __init__(self, user, action_name):
        Error.SimpleError.__init__(self, "Permission Denied",
                                   "User %s cannot access action %s" % (user, action_name))



class User:
    def __init__(self, db, login, permissions, configuration):
        self._db = db
        self.login = login
        self.permissions = permissions
        self.configuration = configuration    
        
    def delConfigValue(self, key):
        login = self._db.escape(self.login)

        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE login = %s AND name = %s" %
                       (login, self._db.escape(key)))

        try: self.configuration.pop(key)
        except KeyError: pass

    def delConfigValueMatch(self, key):
        login = self._db.escape(self.login)

        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE login = %s AND name LIKE %s"
                       % (login, self._db.escape(key)))

        for k in self.configuration.keys():
            if k.find(key) != -1:
                self.configuration.pop(key)
    
    def getConfigValue(self, key):
        return self.configuration[key]
    
    def setConfigValue(self, key, value):
        k = self._db.escape(key)
        login = self._db.escape(self.login)
        
        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE login = %s AND name = %s" % (login, k))
        if not type(value) is list:
            self._db.query("INSERT INTO Prewikka_User_Configuration (login, name, value) VALUES (%s,%s,%s)" %
                           (login, k, self._db.escape(str(value))))
        else:
            for v in value:
                self._db.query("INSERT INTO Prewikka_User_Configuration (login, name, value) VALUES (%s,%s,%s)" %
                           (login, k, self._db.escape(v)))

        self.configuration[key] = value
        
    def has(self, perm):
        if type(perm) in (list, tuple):
            return filter(lambda p: self.has(p), perm) == perm

        return perm in self.permissions
