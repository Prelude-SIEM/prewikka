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

import os, os.path
import errno
import shutil

from prewikka import Storage, Auth, User


class DirectoryStorage(Storage.Storage):
    def __init__(self, config):
        self._base_dir = config.getOptionValue("directory")
        if not self._base_dir:
            if os.access("/var", os.W_OK):
                self._base_dir = "/var/prewikka"
            else:
                self._base_dir = "%s/.prewikka" % os.getenv("HOME")
        self._users_dir = self._base_dir + "/users"
        self._sessions_dir = self._base_dir + "/sessions"
        os.path.exists(self._base_dir) or os.mkdir(self._base_dir)
        os.path.exists(self._users_dir) or os.mkdir(self._users_dir)

    def _getUserPath(self, login):
        return "%s/%s" % (self._users_dir, login)

    def _getUserFilePath(self, login, file):
        return "%s/%s" % (self._getUserPath(login), file)

    def _openUserFile(self, login, file, mode="r"):
        try:
            return open(self._getUserFilePath(login, file), mode)
        except IOError, e:
            if e.errno == errno.ENOENT and not os.path.exists(self._getUserPath(login)):
                raise Storage.StorageError("unknown user '%s'" % login)
            raise

    def _getSessionFile(self, sessionid):
        return "%s/%s" % (self._sessions_dir, sessionid)

    def hasUser(self, login):
        return os.path.exists(self._getUserPath(login))

    def createUser(self, login):
        os.mkdir(self._getUserPath(login))
        self._openUserFile(login, "permissions", "w")

    def deleteUser(self, login):
        shutil.rmtree(self._getUserPath(login))

    def getUsers(self):
        return os.listdir(self._users_dir)

    def setPassword(self, login, password):
        file = self._openUserFile(login, "password", "w")
        file.write(password)
        file.close()

    def getPassword(self, login):
        file = self._openUserFile(login, "password")
        password = file.read()
        file.close()
        return password

    def hasPassword(self, login):
        if not os.path.exists(self._getUserFilePath(login, "password")):
            if not os.path.exists(self._getUserPath(login)):
                raise Storage.StorageError()
            return False
        return True

    def setPermissions(self, login, permissions):
        file = self._openUserFile(login, "permissions", "w")
        for perm in permissions:
            print >> file, perm
        file.close()

    def getPermissions(self, login):
        permissions = [ ]
        file = self._openUserFile(login, "permissions")
        for perm in file.xreadlines():
            perm = perm.rstrip()
            if not perm in User.ALL_PERMISSIONS:
                raise Storage.StorageBackendError("invalid permission '%s'" % perm)
            permissions.append(perm)
        file.close()
        
        return permissions

    def createSession(self, sessionid, user, t):
        os.path.exists(self._sessions_dir) or os.mkdir(self._sessions_dir)
        file = open(self._getSessionFile(sessionid), "w")
        print >> file, user, t,
        file.close()

    def getSession(self, sessionid):
        try:
            file = open(self._getSessionFile(sessionid))
        except IOError, e:
            if e.errno == errno.ENOENT:
                raise Storage.StorageError("invalid sessionid '%s'" % sessionid)
            raise

        user, t = file.read().split()

        return user, int(t)

    def deleteSession(self, sessionid):
        os.remove(self._getSessionFile(sessionid))

    def getSessions(self):
        if not os.path.exists(self._sessions_dir):
            return [ ]
        return os.listdir(self._sessions_dir)



def load(core, config):
    storage = DirectoryStorage(config)
    core.registerStorage(storage)
