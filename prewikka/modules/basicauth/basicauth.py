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

import time
import random
import md5

from prewikka import Auth


class PasswordDatabase(dict):
    def __init__(self, filename):
        dict.__init__(self)
        self._filename = filename

    def load(self):
        file = open(self._filename, "r")
        for line in file.readlines():
            login, password = line.rstrip().split()
            self[login] = password
        file.close()

    def save(self):
        file = open(self._filename, "w")
        for login, password in self.items():
            print >> file, login, passwd
        file.close()



class SessionDatabase(dict):
    def __init__(self, filename):
        dict.__init__(self)
        self._filename = filename
        
    def load(self):
        file = open(self._filename, "r")
        for line in file.readlines():
            sessionid, login, expiration = line.rstrip().split()
            self[sessionid] = [ login, expiration ]
        file.close()

    def save(self):
        file = open(self._filename, "w")
        for sessionid in self.keys():
            login, expiration = self[sessionid]
            print >> file, sessionid, login, expiration
        file.close()
        
    def add(self, sessionid, login, t):
        self[sessionid] = login, t



class BasicAuth(Auth.LoginPasswordAuth):
    def __init__(self, core, config):
        Auth.LoginPasswordAuth.__init__(self, core)
        self._sessions_file = config.get("session_file", "basic_sessions")
        self._passwd_file = config.get("password_file", "basic_passwords")
        
    def getSessionData(self, sessionid):
        sessions = SessionDatabase(self._sessions_file)
        sessions.load()
        
        if not sessionid in sessions.keys():
            raise Auth.SessionError
        
        name, t = sessions[sessionid]
        
        return name, int(t)
    
    def checkLoginPassword(self, login, password):
        passwords = PasswordDatabase(self._passwd_file)
        passwords.load()
        if login in passwords and passwords[login] == password:
            t = int(time.time())
            sessionid = md5.new(str(t * random.random())).hexdigest()
            sessions = SessionDatabase(self._sessions_file)
            sessions.load()
            sessions.add(sessionid, login, t)
            sessions.save()
            return sessionid

        raise Auth.AuthError
        


def load(core, config):
    auth = BasicAuth(core, config)
    core.registerAuth(auth)
