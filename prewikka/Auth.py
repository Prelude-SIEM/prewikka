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


class AuthError(PrewikkaError):
    def __init__(self, message="", arguments={}):
        self.dataset = DataSet.DataSet()
        self.dataset["message"] = message
        self.dataset["arguments"] = arguments.items()
        self.template = "LoginPasswordForm"



class Auth:
    def __init__(self, env):
        if not env.storage:
            raise Exception("You must have a storage backend in order to use authentication.")
        self.storage = env.storage
        self.log = env.log
        
        users = self.storage.getUsers()
        
        has_user_manager = False
        for login in users:
            user = self.storage.getUser(login)
            if User.PERM_USER_MANAGEMENT in user.permissions:
                has_user_manager = True
                break
            
        if not has_user_manager:
            self.storage.createUser(User.ADMIN_LOGIN)
            self.storage.setPermissions(User.ADMIN_LOGIN, User.ALL_PERMISSIONS)
        
    def canSetPassword(self):
        return hasattr(self, "setPassword")

    def canLogout(self):
        return hasattr(self, "logout")



class Session:
    def __init__(self, expiration):
        self._expiration = expiration
    
    def checkSession(self, request):
        if not request.input_cookie.has_key("sessionid"):
            raise AuthError(arguments=request.arguments)
        
        sessionid = request.input_cookie["sessionid"].value

        try:
            login, t = self.storage.getSession(sessionid)
        except Storage.StorageError:
            self.log(Log.EVENT_INVALID_SESSIONID, request)
            raise AuthError("invalid sessionid", request.arguments)

        if time.time() > t + self._expiration:
            self.storage.deleteSession(sessionid)
            self.log(Log.EVENT_SESSION_EXPIRED, request)
            raise AuthError("session expired", request.arguments)

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
    def __init__(self, env, session_expiration):
        Auth.__init__(self, env)
        Session.__init__(self, session_expiration)

    def getLogin(self, request):
        if request.arguments.has_key("login") and request.arguments.has_key("password"):
            login = request.arguments["login"]
            del request.arguments["login"]
            password = request.arguments["password"]
            del request.arguments["password"]
            try:
                self.checkPassword(login, password)
            except AuthError, e:
                e.dataset["arguments"] = request.arguments.items()
                raise e
            self.createSession(request, login)
            return login

        return self.checkSession(request)

    def logout(self, request):
        self.deleteSession(request)
        raise AuthError()
