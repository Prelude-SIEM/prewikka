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


from prewikka import User


class StorageError(Exception):
    pass



class StorageBackendError(Exception):
    pass



class StorageInvalidError(StorageError):
    def __init__(self, resource):
        self._resource = resource
    
    def __str__(self):
        return "invalid %s '%s'" % (self.type, self._resource)



class StorageInvalidUserError(StorageInvalidError):
    type = "user"



class StorageInvalidSessionError(StorageInvalidError):
    type = "session"



class StorageInvalidFilterError(StorageInvalidError):
    type = "filter"



class Storage:
    def deleteExpiredSessions(self, expiration_time):
        sessions = self.getSessions()
        for sessionid in sessions:
            user, t = self.getSession(sessionid)
            if t < expiration_time:
                self.deleteSession(sessionid)

    def getUser(self, login):
        return User.User(login, self.getPermissions(login))
