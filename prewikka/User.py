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


from prewikka import Error, Log


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


class PermissionDeniedError(Error.PrewikkaUserError):
    def __init__(self, action_name):
        Error.PrewikkaUserError.__init__(self, _("Permission Denied"),
                                         _("Access to view '%s' forbidden") % action_name, log=Log.WARNING)
                                         
                                         
class User:
    def __init__(self, db, login, permissions, configuration):
        self._db = db
        self.login = login
        self.permissions = permissions
        self.configuration = configuration    
        
    def delConfigValue(self, view, key=None):
        login = self._db.escape(self.login)
        
        if key != None:
            qstr = " AND name = %s" % (self._db.escape(key))
        else:
            qstr = ""
            
        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE view = %s AND login = %s%s" %
                       (self._db.escape(view), login, qstr))

        try: self.configuration[view].pop(key)
        except KeyError: pass

    def delConfigValueMatch(self, view, key):
        login = self._db.escape(self.login)
        
        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE view = %s AND login = %s AND name LIKE %s"
                       % (self._db.escape(view), login, self._db.escape(key)))

        for k in self.configuration[view].keys():
            if k.find(key) != -1:
                self.configuration.pop(key)
    
    def getConfigValue(self, view, key):
        return self.configuration[view][key]
    
    def setConfigValue(self, view, key, value):
        k = self._db.escape(key)
        v = self._db.escape(view)
        login = self._db.escape(self.login)
        
        self._db.query("DELETE FROM Prewikka_User_Configuration WHERE view = %s AND login = %s AND name = %s" % (v, login, k))
        if not type(value) is list:
            self._db.query("INSERT INTO Prewikka_User_Configuration (view, login, name, value) VALUES (%s,%s,%s,%s)" %
                           (v, login, k, self._db.escape(str(value))))
        else:
            for val in value:
                self._db.query("INSERT INTO Prewikka_User_Configuration (view, login, name, value) VALUES (%s, %s,%s,%s)" %
                           (v, login, k, self._db.escape(val)))

        if not self.configuration.has_key(view):
            self.configuration[view] = { }
        
        self.configuration[view][key] = value
        
    def has(self, perm):
        if type(perm) in (list, tuple):
            return filter(lambda p: self.has(p), perm) == perm

        return perm in self.permissions
