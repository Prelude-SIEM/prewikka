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
import random
import md5

from prewikka import view, Log, DataSet, User
import prewikka.Error
from prewikka import utils


class PermissionsParameters:
    def register(self):
        for perm in User.ALL_PERMISSIONS:
            self.optional(perm, str)
            
    def normalize(self):
        for perm in User.ALL_PERMISSIONS:
            if self.has_key(perm) and self[perm] != "on":
                raise view.InvalidParameterValueError(perm, self[perm])



class PasswordParameters:
    def register(self):
        self.mandatory("password1", str)
        self.mandatory("password2", str)

    def normalize(self):
        if self["password1"] != self["password2"]:
            raise view.ParameterError("passwords mismatch")
        self["password"] = self["password1"]



class UserParameters(view.Parameters):
    def register(self):
        self.mandatory("login", str)



class UserAddParameters(UserParameters, PermissionsParameters, PasswordParameters):
    def register(self):
        UserParameters.register(self)
        PermissionsParameters.register(self)
        PasswordParameters.register(self)

    def normalize(self):
        UserParameters.normalize(self)
        PermissionsParameters.normalize(self)
        PasswordParameters.normalize(self)



class UserSettingsParameters(view.Parameters):
    def register(self):
        self.optional("login", str)



class UserSettingsModifyParameters(view.Parameters):
    def register(self):
        self.optional("login", str)
        for perm in User.ALL_PERMISSIONS:
            self.optional(perm, str)
        self.optional("password_current", str)
        self.optional("password_new", str)
        self.optional("password_new_confirmation", str)

    def normalize(self):
        self["permissions"] = [ ]
        for perm in User.ALL_PERMISSIONS:
            if self.get(perm) == "on":
                self["permissions"].append(perm)
        


class UserDeleteParameters(view.Parameters):
    def register(self):
        self.optional("users", list, [ ])
    


class UserListing(view.View):
    view_name = "user_listing"
    view_parameters = view.Parameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "UserListing"

    def render(self):
        self.dataset["add_form_hiddens"] = [("view", "user_add_form")]
        self.dataset["permissions"] = User.ALL_PERMISSIONS
        self.dataset["can_set_password"] = self.env.auth and self.env.auth.canSetPassword()
        self.dataset["users"] = [ ]

        logins = self.env.db.getUserLogins()
        logins.sort()
        for login in logins:
            user = self.env.db.getUser(login)
            tmp = { }
            tmp["login"] = user.login
            tmp["settings_link"] = utils.create_link("user_settings_display", { "login": login })
            tmp["permissions"] = map(lambda perm: user.has(perm), User.ALL_PERMISSIONS)
            self.dataset["users"].append(tmp)



class UserAddForm(view.View):
    view_name = "user_add_form"
    view_parameters = view.Parameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "PropertiesChangeForm"

    def render(self):
        self.dataset["submit"] = "add"
        self.dataset["hiddens"] = [ ("view", "user_add") ]
        self.dataset["properties"] = [ utils.text_property("Login", "login") ]
        if self.env.auth.canSetPassword():
            self.dataset["properties"].extend((utils.password_property("Password", "password1"),
                                               utils.password_property("Password confirmation", "password2")))
        for perm in User.ALL_PERMISSIONS:
            self.dataset["properties"].append(utils.boolean_property(perm, perm))



class UserAdd(UserListing):
    view_name = "user_add"
    view_parameters = UserAddParameters

    def render(self):
        login = self.parameters["login"]

        self.env.db.createUser(login)
        
        if self.env.auth.canSetPassword():
            self.env.auth.setPassword(login, self.parameters["password"])
        
        permissions = filter(lambda perm: self.parameters.has_key(perm), User.ALL_PERMISSIONS)
        self.env.db.setPermissions(login, permissions)

        self.parameters.clear()
        UserListing.render(self)



class UserDelete(UserListing):
    view_name = "user_delete"
    view_parameters = UserDeleteParameters

    def render(self):
        for user in self.parameters["users"]:
            self.env.db.deleteUser(user)
        
        self.parameters.clear()
        UserListing.render(self)



class UserSettingsDisplay(view.View):
    view_name = "user_settings_display"
    view_parameters = UserSettingsParameters
    view_permissions = [ ]
    view_template = "UserSettings"

    def render(self):
        login = self.parameters.get("login", self.user.login)
        
        self.dataset["management_mode"] = self.user.has(User.PERM_USER_MANAGEMENT)
        self.dataset["can_change_password"] = self.env.auth.canSetPassword()
        self.dataset["current_user"] = self.user.login
        self.dataset["user.login"] = login
        self.dataset["user.permissions"] = [ ]
        permissions = self.env.db.getPermissions(login)
        for perm in User.ALL_PERMISSIONS:
            self.dataset["user.permissions"].append((perm, perm in permissions))



class UserSettingsModify(UserSettingsDisplay):
    view_name = "user_settings_modify"
    view_parameters = UserSettingsModifyParameters
    view_permissions = [ ]

    def render(self):
        login = self.parameters.get("login", self.user.login)
        
        if self.user.has(User.PERM_USER_MANAGEMENT):
            self.env.db.setPermissions(login, self.parameters["permissions"])
            if login == self.user.permissions:
                self.user.permissions = self.parameters["permissions"]

        if self.parameters.has_key("password_new") and self.parameters.has_key("password_new_confirmation"):
            if self.parameters.has_key("password_current"):
                self.env.auth.checkPassword(login, self.parameters["password_current"])

            if self.parameters["password_new"] != self.parameters["password_new_confirmation"]:
                raise prewikka.Error.SimpleError("Password Error", "passwords mismatch")

            self.env.auth.setPassword(login, self.parameters["password_new"])

        UserSettingsDisplay.render(self)
