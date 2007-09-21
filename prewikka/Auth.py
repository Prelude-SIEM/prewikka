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

import time
import md5
import random

from prewikka.Error import PrewikkaError, PrewikkaUserError
from prewikka import DataSet
from prewikka import Database
from prewikka import Log
from prewikka import User


class AuthError(PrewikkaUserError):
    def __init__(self, arguments={}, message=_("Authentication failed"), log=Log.ERROR, log_user=None):
        PrewikkaUserError.__init__(self, None, message, log=log, log_user=log_user)
        self.template = "LoginPasswordForm"


class AuthSessionInvalid(AuthError):
    def __init__(self, arguments={}, message=_("Invalid session"), login=None, log=None):
        AuthError.__init__(self, arguments, message, log=log, log_user=login)



class AuthSessionExpired(AuthError):
    def __init__(self, login, arguments={}, message=_("Session expired")):
        AuthError.__init__(self, arguments, message, log=Log.ERROR, log_user=login)



class Session:
    def __init__(self, expiration):
        self._expiration = expiration

    def setSession(self, request, sessionid):
        request.addCookie("sessionid", sessionid, self._expiration * 3)

    def checkSession(self, request):
        if not request.input_cookie.has_key("sessionid"):
            raise AuthSessionInvalid()

        sessionid = request.input_cookie["sessionid"].value

        try:
            login, t = self.db.getSession(sessionid)
        except Database.DatabaseInvalidSessionError:
            raise AuthSessionInvalid(log=Log.ERROR)

        now = int(time.time())

        if now - t > self._expiration:
            self.db.deleteSession(sessionid)
            raise AuthSessionExpired(login)

        self.db.updateSession(sessionid, now)
        self.setSession(request, sessionid)

        return login

    def createSession(self, request, login):
        t = int(time.time())
        self.db.deleteExpiredSessions(t - self._expiration)
        sessionid = md5.new(str(t * random.random())).hexdigest()
        self.db.createSession(sessionid, login, t)
        self.setSession(request, sessionid)

    def deleteSession(self, request):
        self.db.deleteSession(request.input_cookie["sessionid"].value)


class Auth:
    def __init__(self, env):
        self.db = env.db
        self.log = env.log

    def canCreateUser(self):
        return hasattr(self, "createUser")

    def canDeleteUser(self):
        return hasattr(self, "deleteUser")

    def canSetPassword(self):
        return hasattr(self, "setPassword")

    def canLogout(self):
        return hasattr(self, "logout")

    def getUserLogins(self):
        return self.db.getUserLogins()

    def getUser(self, request):
        pass


class LoginPasswordAuth(Auth, Session):
    def __init__(self, env, session_expiration):
        Auth.__init__(self, env)
        Session.__init__(self, session_expiration)

    def getUser(self, request):
        if request.arguments.has_key("_login"):
            login = request.arguments["_login"]
            del request.arguments["_login"]
            password = request.arguments.get("_password", "")
            try:
                del request.arguments["_password"]
            except KeyError:
                pass

            self.checkPassword(login, password)
            self.createSession(request, login)
            self.log.info("User login", request, login)
        else:
            login = self.checkSession(request)

        return self.db.getUser(login)

    def logout(self, request):
        login = self.checkSession(request)
        self.deleteSession(request)

        raise AuthSessionInvalid(message=_("Logged out"), login=login, log=Log.INFO)
