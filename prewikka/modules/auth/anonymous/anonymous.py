# Copyright (C) 2007-2012 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


from prewikka import Auth, User

class AnonymousAuth(Auth.Auth):
    def __init__(self, env):
        Auth.Auth.__init__(self, env)

        if not self.db.hasUser("anonymous"):
            self.db.createUser("anonymous")

        self._permissions = User.ALL_PERMISSIONS[:]
        self._permissions.remove(User.PERM_USER_MANAGEMENT)
        self.db.setPermissions("anonymous", self._permissions)

    def getUser(self, request):
        return User.User(self.db, "anonymous", self.db.getLanguage("anonymous"), self._permissions, self.db.getConfiguration("anonymous"))


def load(env, config):
    return AnonymousAuth(env)
