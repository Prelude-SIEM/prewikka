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


import md5

from prewikka import Auth, User, Storage


class MyLoginPasswordAuth(Auth.LoginPasswordAuth):
    def __init__(self, core, config):
        Auth.LoginPasswordAuth.__init__(self,
                                        core.storage,
                                        int(config.getOptionValue("expiration", 60)) * 60)
        
        if not self.storage.hasPassword(User.ADMIN_LOGIN):
            self.setPassword(User.ADMIN_LOGIN, User.ADMIN_LOGIN)
            
    def _hash(self, data):
        return md5.new(data).hexdigest()
    
    def handle_login(self, login, password):
        try:
            real_password = self.storage.getPassword(login)
        except Storage.StorageError:
            raise Auth.AuthError("invalid login '%s'" % login)
        
        if self._hash(password) != real_password:
            raise Auth.AuthError("invalid password for login '%s'" % login)

    def setPassword(self, login, password):
        self.storage.setPassword(login, self._hash(password))


def load(core, config):
    auth = MyLoginPasswordAuth(core, config)
    core.registerAuth(auth)
