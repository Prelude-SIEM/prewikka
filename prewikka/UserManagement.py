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

from prewikka import Log, Action, DataSet, User
import prewikka.Error
from prewikka.templates import LoginPasswordForm, PropertiesChangeForm
from prewikka.templates import UserListing
from prewikka import utils

class PermissionActionParameters:
    def register(self):
        for perm in User.ALL_PERMISSIONS:
            self.registerParameter(perm, str)
        
    def has(self, perm):
        return self.hasParameter(perm)
    
    def getPermissions(self):
        return filter(lambda perm: self.has(perm), User.ALL_PERMISSIONS)
    
    def check(self):
        for perm in User.ALL_PERMISSIONS:
            if self.hasParameter(perm) and self[perm] != "on":
                raise Action.ActionParameterInvalidError(perm)



class AddUserActionParameters(Action.ActionParameters, PermissionActionParameters):
    def register(self):
        PermissionActionParameters.register(self)
        self.registerParameter("login", str, required=True)
        self.registerParameter("password1", str, required=True)
        self.registerParameter("password2", str, required=True)
        
    def getLogin(self):
        return self["login"]

    def getPassword(self):
        return self["password1"]
    
    def check(self):
        Action.ActionParameters.check(self)
        PermissionActionParameters.check(self)



class UserActionParameters(Action.ActionParameters):
    def register(self):
        self.registerParameter("login", str, required=True)
        
    def getLogin(self):
        return self["login"]
    
    def setLogin(self, login):
        self["login"] = login



class ChangePasswordActionParameters(UserActionParameters):
    def register(self):
        UserActionParameters.register(self)
        self.registerParameter("password1", str, required=True)
        self.registerParameter("password2", str, required=True)
        
    def getPassword(self):
        return self["password1"]
        
    def check(self):
        UserActionParameters.check(self)
        if self["password1"] != self["password2"]:
            raise Action.ActionParameterError()



class ChangePermissionsActionParameters(UserActionParameters, PermissionActionParameters):
    def register(self):
        UserActionParameters.register(self)
        PermissionActionParameters.register(self)
        
    def check(self):
        UserActionParameters.check(self)
        PermissionActionParameters.check(self)



class UserManagement(Action.ActionGroup):
    def __init__(self, core):
        Action.ActionGroup.__init__(self, "user_management")
        self.core = core
        self.registerSlot("user_listing", Action.ActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("user_add_form", Action.ActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("user_add", AddUserActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("change_password_form", UserActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("change_password", ChangePasswordActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("change_permissions_form", UserActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("change_permissions", ChangePermissionsActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.registerSlot("user_delete", UserActionParameters, [ User.PERM_USER_MANAGEMENT ])
        self.core.interface.registerConfigurationSection("Users", self.slots["user_listing"].path)

    def _setView(self, dataset):
        dataset["interface.active_section"] = "Configuration"
        dataset["interface.tabs"] = [("Users", utils.create_link(self.slots["user_listing"].path))]
        dataset["interface.active_tab"] = "Users"
        
    def _createUserActionHiddens(self, action_name, parameters=[]):
        return [("action", action_name)] + parameters
        
    def handle_user_listing(self, request):
        dataset = request.dataset
        dataset["add_form_hiddens"] = self._createUserActionHiddens(self.slots["user_add_form"].path)
        dataset["permissions"] = User.ALL_PERMISSIONS
        dataset["can_set_password"] = self.core.auth and self.core.auth.canSetPassword()
        dataset["users"] = [ ]

        users = self.core.storage.getUsers()
        users.sort()
        for login in users:
            user = self.core.storage.getUser(login)
            parameters = [("login", user.login)]
            tmp = { }
            tmp["login"] = user.login
            tmp["permissions"] = map(lambda perm: user.has(perm), User.ALL_PERMISSIONS)
            tmp["delete_form_hiddens"] = self._createUserActionHiddens(self.slots["user_delete"].path, parameters)
            tmp["password_form_hiddens"] = self._createUserActionHiddens(self.slots["change_password_form"].path,parameters)
            tmp["permissions_form_hiddens"] = self._createUserActionHiddens(self.slots["change_permissions_form"].path, parameters)
            dataset["users"].append(tmp)

        self._setView(dataset)

        return UserListing.UserListing

    def handle_user_add_form(self, request):
        dataset = request.dataset
        dataset["submit"] = "add"
        dataset["hiddens"] = [ ("action", self.slots["user_add"].path) ]
        dataset["properties"] = [ utils.text_property("Login", "login") ]
        if self.core.auth.canSetPassword():
            dataset["properties"].extend((utils.password_property("Password", "password1"),
                                          utils.password_property("Password confirmation", "password2")))
        for perm in User.ALL_PERMISSIONS:
            dataset["properties"].append(utils.boolean_property(perm, perm))

        self._setView(dataset)
        
        return PropertiesChangeForm.PropertiesChangeForm
    
    def handle_user_add(self, request):
        login = request.parameters.getLogin()
        
        self.core.storage.createUser(login)
        if self.core.auth.canSetPassword():
            self.core.auth.setPassword(login, request.parameters.getPassword())
        self.core.storage.setPermissions(login, request.parameters.getPermissions())

        request.parameters = Action.ActionParameters()

        return self.handle_user_listing(request)
        
    def handle_user_delete(self, request):
        self.core.storage.deleteUser(request.parameters.getLogin())

        request.parameters = Action.ActionParameters()

        return self.handle_user_listing(request)
    
    def handle_change_password_form(self, request):
        if not self.core.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        
        dataset = request.dataset
        dataset["submit"] = "change"
        dataset["hiddens"] = [ ("action", self.slots["change_password"].path),
                               ("login", request.parameters.getLogin()) ]
        dataset["properties"] = [ utils.password_property("Password", "password1"),
                                  utils.password_property("Password confirmation", "password2") ]

        self._setView(dataset)
        
        return PropertiesChangeForm.PropertiesChangeForm
    
    def handle_change_password(self, request):
        if not self.core.auth.canSetPassword():
            raise Error.SimpleError("permission denied")
        self.core.auth.setPassword(request.parameters.getLogin(),
                                   request.parameters.getPassword())

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)
    
    def handle_change_permissions_form(self, request):
        dataset = request.dataset
        dataset["submit"] = "change"
        dataset["hiddens"] = [ ("action", self.slots["change_permissions"].path),
                               ("login", request.parameters.getLogin()) ]
        dataset["properties"] = [ ]
        user = self.core.storage.getUser(request.parameters.getLogin())
        for perm in User.ALL_PERMISSIONS:
            dataset["properties"].append(utils.boolean_property(perm, perm, user.has(perm)))

        self._setView(dataset)

        return PropertiesChangeForm.PropertiesChangeForm
    
    def handle_change_permissions(self, request):
        self.core.storage.setPermissions(request.parameters.getLogin(),
                                         request.parameters.getPermissions())

        request.parameters = Action.ActionParameters()
        
        return self.handle_user_listing(request)
