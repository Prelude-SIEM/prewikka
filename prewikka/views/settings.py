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


import os

from prewikka import view, User, Auth, Error


class PasswordChangeParameters(view.Parameters):
    def register(self):
        self.mandatory("current", str)
        self.mandatory("new", str)
        self.mandatory("confirmation", str)

    def normalize(self):
        view.Parameters.normalize(self)
        if self["new"] != self["confirmation"]:
            raise view.ParameterError("passwords mismatch")



class SettingsDisplay(view.View):
    view_name = "settings_display"
    view_parameters = view.Parameters
    view_permissions = [ ]
    view_template = "SettingsDisplay"

    def render(self):
        self.dataset["login"] = self.user.login
        self.dataset["permissions"] = self.user.permissions
        self.dataset["can_change_password"] = self.env.auth.canSetPassword()



class PasswordChange(SettingsDisplay):
    view_name = "settings_password_change"
    view_parameters = PasswordChangeParameters

    def render(self):
        try:
            self.env.auth.checkPassword(self.user.login, self.parameters["current"])
        except Auth.AuthError:
            raise Error.SimpleError("change password", "bad current password")
        self.env.auth.setPassword(self.user.login, self.parameters["new"])
        SettingsDisplay.render(self)
