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

from prewikka import Log, ParametersNormalizer, DataSet, User
import prewikka.Error
from prewikka.templates import LoginPasswordForm, PropertiesChangeForm
from prewikka.templates import UserListing
from prewikka import utils

class PermissionsPM:
    def register(self):
        for perm in User.ALL_PERMISSIONS:
            self.optional(perm, str)
            
    def normalize(self, parameters):
        for perm in User.ALL_PERMISSIONS:
            if parameters.has_key(perm) and parameters[perm] != "on":
                raise ParametersNormalizer.InvalidValueError(perm, parameters[perm])



class PasswordPM:
    def register(self):
        self.mandatory("password1", str)
        self.mandatory("password2", str)

    def normalize(self, parameters):
        if parameters["password1"] != parameters["password2"]:
            raise ParametersNormalizer.InvalidValueError("password mismatch")
        parameters["password"] = parameters["password1"]



class UserPM(ParametersNormalizer.ParametersNormalizer):
    def register(self):
        self.mandatory("login", str)



class AddUserPM(UserPM, PermissionsPM, PasswordPM):
    def register(self):
        UserPM.register(self)
        PermissionsPM.register(self)
        PasswordPM.register(self)

    def normalize(self, parameters):
        UserPM.normalize(self, parameters)
        PermissionsPM.normalize(self, parameters)
        PasswordPM.normalize(self, parameters)



class ChangePasswordPM(UserPM, PasswordPM):
    def register(self):
        UserPM.register(self)
        PasswordPM.register(self)

    def normalize(self, parameters):
        UserPM.normalize(self, parameters)
        PasswordPM.normalize(self, parameters)



class ChangePermissionsPM(UserPM, PermissionsPM):
    def register(self):
        UserPM.register(self)
        PermissionsPM.register(self)
        
    def normalize(self, parameters):
        UserPM.normalize(self, parameters)
        PermissionsPM.normalize(self, parameters)



class UserManagement:
    default = "user_listing"
    slots = {
        "user_listing": { "template": UserListing.UserListing },
        "user_add_form": { "template": PropertiesChangeForm.PropertiesChangeForm },
        "user_add": { "parameters": AddUserPM(), "template": UserListing.UserListing },
        "change_password_form": { "parameters": UserPM(), "template": PropertiesChangeForm.PropertiesChangeForm },
        "change_password": { "parameters": ChangePasswordPM(), "template": UserListing.UserListing },
        "change_permissions_form": { "parameters": UserPM(), "template": PropertiesChangeForm.PropertiesChangeForm },
        "change_permissions": { "parameters": ChangePermissionsPM(), "template": UserListing.UserListing },
        "user_delete": { "parameters": UserPM(), "template": UserListing.UserListing }
    }

    def __init__(self, env):
        self.env = env

    def _setView(self, dataset):
        dataset["interface.active_section"] = "Configuration"
        dataset["interface.tabs"] = [("Users", utils.create_link("configuration.user_listing"))]
        dataset["interface.active_tab"] = "Users"

    def _createUserActionHiddens(self, action_name, parameters=[]):
        return [("content", action_name)] + parameters
        
    def handle_user_listing(self, request):
        dataset = request.dataset
        dataset["add_form_hiddens"] = self._createUserActionHiddens("configuration.user_add_form")
        dataset["permissions"] = User.ALL_PERMISSIONS
        dataset["can_set_password"] = self.env.auth and self.env.auth.canSetPassword()
        dataset["users"] = [ ]

        users = self.env.storage.getUsers()
        users.sort()
        for login in users:
            user = self.env.storage.getUser(login)
            parameters = [("login", user.login)]
            tmp = { }
            tmp["login"] = user.login
            tmp["permissions"] = map(lambda perm: user.has(perm), User.ALL_PERMISSIONS)
            tmp["delete_form_hiddens"] = self._createUserActionHiddens("configuration.user_delete", parameters)
            tmp["password_form_hiddens"] = self._createUserActionHiddens("configuration.change_password_form", parameters)
            tmp["permissions_form_hiddens"] = self._createUserActionHiddens("configuration.change_permissions_form", parameters)
            dataset["users"].append(tmp)

        self._setView(dataset)

    def handle_user_add_form(self, request):
        dataset = request.dataset
        dataset["submit"] = "add"
        dataset["hiddens"] = [ ("content", "configuration.user_add") ]
        dataset["properties"] = [ utils.text_property("Login", "login") ]
        if self.env.auth.canSetPassword():
            dataset["properties"].extend((utils.password_property("Password", "password1"),
                                          utils.password_property("Password confirmation", "password2")))
        for perm in User.ALL_PERMISSIONS:
            dataset["properties"].append(utils.boolean_property(perm, perm))

        self._setView(dataset)
    
    def handle_user_add(self, request):
        login = request.parameters["login"]
        
        self.env.storage.createUser(login)
        if self.env.auth.canSetPassword():
            self.env.auth.setPassword(login, request.parameters["password"])
        self.env.storage.setPermissions(login, filter(lambda perm: request.parameters.has_key(perm), User.ALL_PERMISSIONS))

        request.parameters = { }

        self.handle_user_listing(request)
        
    def handle_user_delete(self, request):
        self.env.storage.deleteUser(request.parameters["login"])

        request.parameters = { }

        self.handle_user_listing(request)
    
    def handle_change_password_form(self, request):
        if not self.env.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        
        dataset = request.dataset
        dataset["submit"] = "change"
        dataset["hiddens"] = [ ("content", "configuration.change_password"),
                               ("login", request.parameters["login"]) ]
        dataset["properties"] = [ utils.password_property("Password", "password1"),
                                  utils.password_property("Password confirmation", "password2") ]

        self._setView(dataset)
    
    def handle_change_password(self, request):
        if not self.env.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        self.env.auth.setPassword(request.parameters["login"], request.parameters["password"])

        request.parameters = { }
        
        self.handle_user_listing(request)
    
    def handle_change_permissions_form(self, request):
        dataset = request.dataset
        dataset["submit"] = "change"
        dataset["hiddens"] = [ ("content", "configuration.change_permissions"),
                               ("login", request.parameters["login"]) ]
        dataset["properties"] = [ ]
        user = self.env.storage.getUser(request.parameters["login"])
        for perm in User.ALL_PERMISSIONS:
            dataset["properties"].append(utils.boolean_property(perm, perm, user.has(perm)))

        self._setView(dataset)
    
    def handle_change_permissions(self, request):
        self.env.storage.setPermissions(request.parameters["login"],
                                        filter(lambda perm: request.parameters.has_key(perm), User.ALL_PERMISSIONS))

        request.parameters = { }
        
        self.handle_user_listing(request)
