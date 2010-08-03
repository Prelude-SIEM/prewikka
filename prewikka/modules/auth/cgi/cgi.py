# Copyright (C) 2006 PreludeIDS Technologies. All Rights Reserved.
# Author: Tilman Baumann <tilman.baumann@collax.com>
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

import os
from prewikka import Auth, User, Database, utils


class CGIAuth(Auth.Auth):
    def __init__(self, env, config):
        Auth.Auth.__init__(self, env)

        default_admin_user = config.getOptionValue("default_admin_user", None)
        if default_admin_user != None:
            if not self.db.hasUser(default_admin_user):
                self.db.createUser(default_admin_user)

            self.db.setPermissions(default_admin_user, User.ALL_PERMISSIONS)

    def deleteUser(self, login):
        self.db.deleteUser(login)

    def getUser(self, request):
        user = request.getRemoteUser()
        if not user:
            raise Auth.AuthError(message=_("CGI Authentication failed: no user specified."))

        user = utils.toUnicode(user)

        # Create the user in the Prewikka database, so that its permission
        # might be modified by another administrative user.
        if not self.db.hasUser(user):
            self.db.createUser(user)

        return self.db.getUser(user)



def load(env, config):
    return CGIAuth(env, config)


