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

from prewikka import Interface, Views
from prewikka.templates import LoginPasswordForm
from prewikka import Interface 


class Error(Exception):
    pass


class SessionError(Error):
    pass


class AuthError(Error):
    pass


class LoginError(Error):
    pass



class Auth:
    def __init__(self, core):
        self._core = core

    def check(self, request):
        pass



class LoginPasswordActionParameters(Interface.ActionParameters):
    def register(self):
        self.registerParameter("login", str)
        self.registerParameter("password", str)
        
    def getLogin(self):
        return self["login"]
    
    def getPassword(self):
        return self["password"]
    
    def check(self):
        return self.hasParameter("login") and self.hasParameter("password")



class LoginPasswordPromptView(Views.TopView):
    def build(self, data):
        Views.TopView.build(self, str(LoginPasswordForm.LoginPasswordForm()))



class LoginPasswordAuth(Auth):
    def __init__(self, core):
        Auth.__init__(self, core)
        self._expiration = 1
        self._core = core
        
    def setExpiration(self, expiration):
        self._expiration = expiration
        
    def check(self, request):
        if request.input_cookie.has_key("sessionid"):
            try:
                user, t = self.getSessionData(request.input_cookie["sessionid"].value)
            except SessionError:
                # TODO: log invalid sessions
                raise AuthError
            if time.time() - t < self._expiration * 60:
                return user
        raise AuthError
    
    def getLoginScreen(self, request):
        view = LoginPasswordPromptView(self._core)
        view.build(self)
        return str(view)
    
    def logout(self, request):
        pass

    def login(self, login, password, request):
        session = self.checkLoginPassword(login, password)
        request.output_cookie["sessionid"] = session
        
    def process(self, core, parameters, request):
        return self.login(core, parameters, request)
    


class DefaultAuth(Auth):
    def check(self, request):
        return "anonymous"
