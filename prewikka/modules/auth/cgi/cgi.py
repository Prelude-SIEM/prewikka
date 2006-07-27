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


class CGIAuth(Auth.AnonymousAuth):
    def __init__(self, env, config):
	# Need to call Auth.Auth's init because the init of 
	# our superclass Auth.AnonymousAuth does not set env.
        Auth.Auth.__init__(self, env)
	self.config = config

    def getUser(self, request):
	user = os.environ.get("REMOTE_USER", None)        
    	if not user:
	    raise Auth.AuthError(message="CGI Authentication failed: no user specified.")
        
        return User.User(self.db, user, User.ALL_PERMISSIONS, self.config)



def load(env, config):
    return CGIAuth(env, config)


