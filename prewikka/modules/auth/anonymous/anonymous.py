# Copyright (C) 2007 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


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
