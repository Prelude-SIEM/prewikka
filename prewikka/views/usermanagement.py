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
                raise ParametersNormalizer.InvalidValueError(perm, self[perm])



class PasswordParameters:
    def register(self):
        self.mandatory("password1", str)
        self.mandatory("password2", str)

    def normalize(self):
        if self["password1"] != self["password2"]:
            raise ParametersNormalizer.InvalidValueError("password mismatch")
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



class PasswordChangeParameters(UserParameters, PasswordParameters):
    def register(self):
        UserParameters.register(self)
        PasswordParameters.register(self)

    def normalize(self):
        UserParameters.normalize(self)
        PasswordParameters.normalize(self)



class PermissionsChangeParameters(UserParameters, PermissionsParameters):
    def register(self):
        UserParameters.register(self)
        PermissionsParameters.register(self)
        
    def normalize(self, ):
        UserParameters.normalize(self)
        PermissionsParameters.normalize(self)



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

        users = self.env.storage.getUsers()
        users.sort()
        for login in users:
            user = self.env.storage.getUser(login)
            tmp = { }
            tmp["login"] = user.login
            tmp["permissions"] = map(lambda perm: user.has(perm), User.ALL_PERMISSIONS)
            tmp["delete_form_hiddens"] = [("view", "user_delete"), ("login", user.login)]
            tmp["password_form_hiddens"] = [("view", "user_password_change_form"),
                                            ("login", user.login)]
            tmp["permissions_form_hiddens"] = [("view", "user_permissions_change_form"),
                                               ("login", user.login)]
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

        self.env.storage.createUser(login)
        
        if self.env.auth.canSetPassword():
            self.env.auth.setPassword(login, self.parameters["password"])
        
        permissions = filter(lambda perm: self.parameters.has_key(perm), User.ALL_PERMISSIONS)
        self.env.storage.setPermissions(login, permissions)

        self.parameters.clear()
        UserListing.render(self)



class UserDelete(UserListing):
    view_name = "user_delete"
    view_parameters = UserParameters

    def render(self):
        self.env.storage.deleteUser(self.parameters["login"])
        
        self.parameters.clear()
        UserListing.render(self)



class PasswordChangeForm(view.View):
    view_name = "user_password_change_form"
    view_parameters = UserParameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "PropertiesChangeForm"
    
    def render(self):
        if not self.env.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        
        self.dataset["submit"] = "change"
        self.dataset["hiddens"] = [ ("view", "user_password_change"),
                                    ("login", self.parameters["login"]) ]
        self.dataset["properties"] = [ utils.password_property("Password", "password1"),
                                       utils.password_property("Password confirmation", "password2") ]



class PasswordChange(UserListing):
    view_name = "user_password_change"
    view_parameters = PasswordChangeParameters

    def render(self):
        if not self.env.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        self.env.auth.setPassword(self.parameters["login"], self.parameters["password"])

        self.parameters.clear()
        UserListing.render(self)



class PermissionsChangeForm(view.View):
    view_name = "user_permissions_change_form"
    view_parameters = UserParameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "PropertiesChangeForm"

    def render(self):
        self.dataset["submit"] = "change"
        self.dataset["hiddens"] = [ ("view", "user_permissions_change"),
                                    ("login", self.parameters["login"]) ]
        self.dataset["properties"] = [ ]
        user = self.env.storage.getUser(self.parameters["login"])
        for perm in User.ALL_PERMISSIONS:
            self.dataset["properties"].append(utils.boolean_property(perm, perm, user.has(perm)))



class PermissionsChange(UserListing):
    view_name = "user_permissions_change"
    view_parameters = PermissionsChangeParameters

    def render(self):
        permissions = filter(lambda perm: self.parameters.has_key(perm), User.ALL_PERMISSIONS)
        self.env.storage.setPermissions(self.parameters["login"], permissions)

        self.parameters.clear()
        UserListing.render(self)
