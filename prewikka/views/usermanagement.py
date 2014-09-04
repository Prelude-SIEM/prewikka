# Copyright (C) 2004-2014 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from prewikka import view, Log, DataSet, User, Auth, Error, localization
from prewikka import utils


class UserSettingsDisplayParameters(view.RelativeViewParameters):
    def register(self):
        self.optional("login", str)
        self.optional("origin", str)



class UserSettingsModifyParameters(UserSettingsDisplayParameters):
    def register(self):

        UserSettingsDisplayParameters.register(self)
        self.optional("language", str)
        self.optional("permissions", list, [])
        self.optional("password_current", str)
        self.optional("password_new", str)
        self.optional("password_new_confirmation", str)

    def normalize(self, view_name, user):
        view.Parameters.normalize(self, view_name, user)


class UserDeleteParameters(view.Parameters):
    def register(self):
        self.optional("users", list, [ ])



class UserListing(view.View):
    view_name = "user_listing"
    view_parameters = view.Parameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "UserListing"

    def hasPermission(self, perm, permlist):
        return perm in permlist

    def render(self):
        self.dataset["backend_can_create"] = self.env.auth.canCreateUser()
        self.dataset["backend_can_delete"] = self.env.auth.canDeleteUser()
        self.dataset["add_form_hiddens"] = [("view", "user_add_form")]
        self.dataset["permissions"] = User.ALL_PERMISSIONS
        self.dataset["can_set_password"] = self.env.auth and self.env.auth.canSetPassword()
        self.dataset["users"] = [ ]

        logins = self.env.auth.getUserLogins()
        logins.sort()
        for login in logins:
            permissions = self.env.db.getPermissions(login)

            tmp = { }
            tmp["login"] = login
            tmp["settings_link"] = utils.create_link("user_settings_display", { "login": login, "origin": self.view_name })
            tmp["permissions"] = map(lambda perm: self.hasPermission(perm, permissions), User.ALL_PERMISSIONS)

            self.dataset["users"].append(tmp)



class UserAddForm(view.View):
    view_name = "user_add_form"
    view_parameters = view.Parameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]
    view_template = "UserSettings"

    def render(self, errmsg=None):
        self.dataset["user.login"] = None
        self.dataset["user.origin"] = "user_listing"

        self.dataset["user.permissions"] = []
        for perm in User.ALL_PERMISSIONS:
            self.dataset["user.permissions"] += [(perm, False)]

        self.dataset["errmsg"] = errmsg
        self.dataset["can_manage_user"] = self.user.has(User.PERM_USER_MANAGEMENT)
        self.dataset["can_change_password"] = self.env.auth.canSetPassword()
        self.dataset["ask_current_password"] = False
        self.dataset["available_languages"] = localization.getLanguagesAndIdentifiers()
        self.dataset["user.language"] = localization._DEFAULT_LANGUAGE

        self.dataset["hiddens"] = [ ("view", "user_add") ]
        self.dataset["properties"] = [ utils.text_property("Login", "login") ]
        if self.env.auth.canSetPassword():
            self.dataset["properties"].extend((utils.password_property("Password", "password1"),
                                               utils.password_property("Password confirmation", "password2")))
        for perm in User.ALL_PERMISSIONS:
            self.dataset["properties"].append(utils.boolean_property(perm, perm))


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
    view_parameters = UserSettingsDisplayParameters
    view_permissions = [ ]
    view_template = "UserSettings"

    def render(self):
        login = self.parameters.get("login", self.user.login)

        if login != self.user.login and not self.user.has(User.PERM_USER_MANAGEMENT):
            raise Error.PrewikkaUserError(_("Permission Denied"), _("Access denied to other users settings"), log=Log.WARNING)

        self.dataset["available_languages"] = localization.getLanguagesAndIdentifiers()
        self.dataset["user.language"] = self.env.db.getLanguage(login) or localization._DEFAULT_LANGUAGE

        self.dataset["ask_current_password"] = (login == self.user.login)
        self.dataset["can_manage_user"] = self.user.has(User.PERM_USER_MANAGEMENT)
        self.dataset["can_change_password"] = self.env.auth.canSetPassword()
        self.dataset["user.login"] = login
        self.dataset["user.permissions"] = [ ]

        if self.parameters.has_key("origin"):
            self.dataset["user.origin"] = self.parameters["origin"]

        permissions = self.env.db.getPermissions(login)
        for perm in User.ALL_PERMISSIONS:
            self.dataset["user.permissions"].append((perm, perm in permissions))



class UserSettingsModify(UserSettingsDisplay):
    view_name = "user_settings_modify"
    view_parameters = UserSettingsModifyParameters
    view_permissions = [ ]

    def render(self):
        login = self.parameters.get("login", self.user.login)

        if login != self.user.login and not self.user.has(User.PERM_USER_MANAGEMENT):
            raise Error.PrewikkaUserError(_("Permission Denied"), _("Cannot modify other users settings"), log=Log.WARNING)

        if self.user.has(User.PERM_USER_MANAGEMENT):
            self.env.db.setPermissions(login, self.parameters["permissions"])
            if login == self.user.login:
                self.user.permissions = self.parameters["permissions"]

        lang = self.parameters["language"]
        if not lang in localization.getLanguagesIdentifiers():
            raise Error.PrewikkaUserError(_("Invalid Language"), _("Specified language does not exist"), log=Log.WARNING)

        if login == self.user.login:
            self.user.setLanguage(lang)

        self.env.db.setLanguage(login, lang)

        if self.parameters.has_key("password_new") and self.parameters.has_key("password_new_confirmation"):
            if login == self.user.login:
                try:
                    self.env.auth.checkPassword(login, self.parameters.get("password_current", ""))
                except Auth.AuthError, e:
                    raise Error.PrewikkaUserError(_("Password Error"), _("Invalid Password specified"))

            if self.parameters["password_new"] != self.parameters["password_new_confirmation"]:
                raise Error.PrewikkaUserError(_("Password Error"), _("Password mismatch"))

            self.env.auth.setPassword(login, self.parameters["password_new"])

        origin = self.parameters.get("origin", None)
        self.parameters.clear()

        if origin:
            self.parameters["origin"] = origin
        self.parameters["login"] = login

        return UserSettingsDisplay.render(self)

class UserSettingsAdd(UserSettingsModify, UserAddForm):
    view_name = "user_settings_add"
    view_parameters =  UserSettingsModifyParameters
    view_permissions = [ User.PERM_USER_MANAGEMENT ]

    def render(self):
        login = self.parameters.get("login", self.user.login)
        if self.env.db.hasUser(login):
            UserAddForm.render(self, _("User %s already exist") % login)
        else:
            self.env.db.createUser(login)
            permissions = filter(lambda perm: self.parameters.has_key(perm), User.ALL_PERMISSIONS)
            self.env.db.setPermissions(login, permissions)
            UserSettingsModify.render(self)
