# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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


import sys
import os.path

import time
import random
import md5
import shelve

from prewikka import UserManagement


class User(UserManagement.User):
    def __init__(self, db, data):
        self.db = db
        self.data = data
        
    def getID(self):
        return self.data["id"]

    def setID(self, id):
        self.data["id"] = id

    def setLogin(self, login):
        self.data["login"] = login

    def getLogin(self):
        return self.data["login"]

    def setPassword(self, password):
        self.data["password"] = self._hashPassword(password)

    def _hashPassword(self, password):
        return md5.new(password).hexdigest()

    def checkPassword(self, password):
        if self._hashPassword(password) != self.data["password"]:
            raise UserManagement.PasswordError()
        
    def addSession(self, sessionid, t):
        self.data["sessions"][sessionid] = t
        
    def getSessionTime(self, sessionid):
        return self.data["sessions"][sessionid]
        
    def removeSession(self, sessionid):
        del self.data["sessions"][sessionid]
        
    def getSessions(self):
        return self.data["sessions"]
    
    def setCapabilities(self, capabilities):
        self.data["capabilities"] = capabilities

    def getCapabilities(self):
        return self.data["capabilities"]
    
    def hasCapability(self, capability):
        return capability in self.data["capabilities"]

    def save(self):
        self.db[str(self.getID())] = self.data
        self.db.sync()



class BasicUserManagement(UserManagement.UserManagement):
    def __init__(self, core, config):
        UserManagement.UserManagement.__init__(self, core, config)
        
        self.db = shelve.open("prewikka_users.db", "c")
        if not self.db:
            user = self.newUser()
            user.setLogin("admin")
            user.setPassword("admin")
            user.setCapabilities(UserManagement.CAPABILITIES_ADMIN)
            user.save()
            self.db.sync()
        
    def __del__(self):
        self.db.close()
        
    def _getNextID(self):
        if not self.db:
            return 0
        
        maxid = 0
        for id in self.db.keys():
            id = int(id)
            if id > maxid:
                maxid = id
        
        return maxid + 1

    def newUser(self):
        data = { }
        id = self._getNextID()
        data["id"] = id
        data["login"] = None
        data["password"] = None
        data["capabilities"] = [ ]
        data["sessions"] = { }
        
        self.db[str(id)] = data
        
        return User(self.db, data)
    
    def getUserBySessionID(self, sessionid):
        for data in self.db.values():
            sessions = data["sessions"]
            keys = sessions.keys()
            keys.sort(lambda x, y: sessions[x] - sessions[y])
            if sessionid in data["sessions"].keys():
                return User(self.db, data)
        
        raise UserManagement.SessionError()
    
    def getUserByLogin(self, login):
        for data in self.db.values():
            if login == data["login"]:
                return User(self.db, data)
            
        raise UserManagement.LoginError()
    
    def getUserByID(self, id):
        return User(self.db, self.db[str(id)])
    
    def getUsers(self):
        return map(lambda id: int(id), self.db.keys())
    
    def getUserSessionIDFromLoginPassword(self, login, password):
        user = None
        for tmp in self.db.values():
            if login == tmp.login:
                user = tmp
                break
        
        if user is None:
            raise UserManagement.LoginError()
        
        password = self._hashPassword(password)
        if password != user.password:
            raise UserManagement.LoginError()
        
        t = int(time.time())
        sessionid = md5.new(str(t * random.random())).hexdigest()
        user.sessions[sessionid] = t

        self.db[str(user.id)] = user
        self.db.sync()
        
        return sessionid
    
    def addUser(self, user):
        user.password = self._hashPassword(user.password)
        user.id = self._getNextID()
        self.db[str(user.id)] = user
        self.db.sync()
        
    def modifyUser(self, user):
        self.db[str(user.id)] = user
        self.db.sync()
        
    def removeUser(self, id):
        del self.db[str(id)]
        self.db.sync()



def load(core, config):
    auth = BasicUserManagement(core, config)
    core.registerAuth(auth)
