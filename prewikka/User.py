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


PERM_IDMEF_VIEW = "IDMEF_VIEW"
PERM_IDMEF_ALTER = "IDMEF_ALTER"
PERM_ADMIN_CONSOLE = "ADMIN_CONSOLE"
PERM_USER_MANAGEMENT = "USER_MANAGEMENT"

ALL_PERMISSIONS = [ PERM_IDMEF_VIEW,
                    PERM_IDMEF_ALTER,
                    PERM_ADMIN_CONSOLE,
                    PERM_USER_MANAGEMENT ]

ADMIN_LOGIN = "admin"


class User:
    def __init__(self, login, permissions):
        self.login = login
        self.permissions = permissions

    def has(self, perm):
        return perm in self.permissions
