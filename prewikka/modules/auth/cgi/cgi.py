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

from prewikka import Auth, User, Database


class CGIAuth(Auth.Auth):
    def getUser(self, request):
	user = request.getRemoteUser()        
    	if not user:
	    raise Auth.AuthError(message=_("CGI Authentication failed: no user specified."))
        
        return User.User(self.db, user, self.db.getLanguage(user), User.ALL_PERMISSIONS, self.db.getConfiguration(user))



def load(env, config):
    return CGIAuth(env)


