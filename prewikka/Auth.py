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


import time
import md5
import random

from prewikka.Error import PrewikkaError, SimpleError
from prewikka import DataSet
from prewikka import Storage
from prewikka import Log
from prewikka import User
from prewikka.templates import LoginPasswordForm


class AuthError(PrewikkaError):
    def __init__(self, message=""):
        self.dataset = DataSet.DataSet()
        self.dataset["message"] = message
        self.template_class = LoginPasswordForm.LoginPasswordForm



class Auth:
    def __init__(self, storage):
        if not storage:
            raise Exception("You must have a storage backend in order to use authentication.")
        self.storage = storage
        login = User.ADMIN_LOGIN
        if not self.storage.hasUser(login):
            self.storage.createUser(login)
            self.storage.setPermissions(login, User.ALL_PERMISSIONS)

    def canSetPassword(self):
        return hasattr(self, "setPassword")

    def canLogout(self):
        return hasattr(self, "logout")



class Session:
    def __init__(self, expiration):
        self._expiration = expiration
    
    def checkSession(self, request):
        if not request.input_cookie.has_key("sessionid"):
            raise AuthError()
        
        sessionid = request.input_cookie["sessionid"].value

        try:
            login, t = self.storage.getSession(sessionid)
        except Storage.StorageError:
            request.env.log(Log.EVENT_INVALID_SESSIONID, request, sessionid)
            raise AuthError("invalid sessionid")

        if time.time() > t + self._expiration:
            self.storage.deleteSession(sessionid)
            request.env.log(Log.EVENT_SESSION_EXPIRED, request, login, sessionid)
            raise AuthError("session expired")

        return login

    def createSession(self, request, login):
        t = int(time.time())
        self.storage.deleteExpiredSessions(t - self._expiration)
        sessionid = md5.new(str(t * random.random())).hexdigest()
        self.storage.createSession(sessionid, login, t)
        request.output_cookie["sessionid"] = sessionid
        request.output_cookie["sessionid"]["expires"] = self._expiration

    def deleteSession(self, request):
        self.storage.deleteSession(request.input_cookie["sessionid"].value)



class LoginPasswordAuth(Auth, Session):
    def __init__(self, storage, session_expiration):
        Auth.__init__(self, storage)
        Session.__init__(self, session_expiration)

    def getLogin(self, request):
        if request.arguments.keys() == ["login", "password"]:
            login = request.arguments["login"]
            password = request.arguments["password"]
            self.handle_login(login, password)
            self.createSession(request, login)
            request.arguments = { }
            return login

        return self.checkSession(request)

    def logout(self, request):
        self.deleteSession(request)
        raise AuthError()
