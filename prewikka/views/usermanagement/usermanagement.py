# Copyright (C) 2004-2020 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>

from __future__ import absolute_import, division, print_function, unicode_literals

import operator
import pkg_resources
from enum import IntEnum

from prewikka import auth, error, hookmanager, localization, log, resource, response, template, usergroup, view
from prewikka.utils.viewhelpers import GridAjaxResponse, GridParameters
from prewikka.database import use_transaction


ReloadEnum = IntEnum("ReloadEnum", "none .commonlisting view window")


class GenericListing(view.View):
    _template = template.PrewikkaTemplate(__name__, "templates/userlisting.mak")

    @hookmanager.register("HOOK_PLUGINS_LOAD")
    def _load(self):
        # Views are loaded before auth/session plugins
        if env.auth != env.session:
            # Do not declare routes with anonymous auth
            view.route("/settings/users", self.list_users, permissions=[N_("USER_MANAGEMENT")],
                       menu=(N_("Access control"), N_("Users")), help="#users", parameters=GridParameters("users"))
            view.route("/settings/groups", self.list_groups, permissions=[N_("GROUP_MANAGEMENT")],
                       menu=(N_("Access control"), N_("Groups")), help="#groups", parameters=GridParameters("users"))

    def _setup_dataset(self, type):
        dset = self._template.dataset()
        dset["type"] = type
        dset["all_permissions"] = sorted(usergroup.ACTIVE_PERMISSIONS)
        return dset

    def list_users(self):
        dset = self._setup_dataset("User")
        dset["backend_can_create"] = env.auth.can_create_user()
        dset["backend_can_delete"] = env.auth.can_delete_user()

        return dset.render()

    def list_groups(self):
        dset = self._setup_dataset("Group")
        dset["backend_can_create"] = env.auth.can_create_group()
        dset["backend_can_delete"] = env.auth.can_delete_group()

        return dset.render()


class GenericListingAjax(view.View):
    def listing(self):
        env.request.user.check("USER_MANAGEMENT")

        objects = self._getObjects(search=env.request.parameters.get("query"))
        reverse = env.request.parameters.get("sort_order") == "desc"
        objects = sorted(objects, key=operator.attrgetter("name"), reverse=reverse)
        page = int(env.request.parameters.get("page", 1))
        nb_rows = int(env.request.parameters.get("rows", 10))

        rows = []

        for obj in objects[(page - 1) * nb_rows:page * nb_rows]:
            permissions = self._getPermissions(obj)

            row = {
                "id": obj.id,
                "cell": {
                    "name": resource.HTMLNode(
                        "a", obj.name,
                        href=url_for(self._link, name=obj.name),
                        title=_(self._title) % obj.name
                    )
                }
            }

            for perm in usergroup.ACTIVE_PERMISSIONS:
                row["cell"][perm] = perm in permissions

            rows.append(row)

        return GridAjaxResponse(rows, len(objects))

    def search(self):
        # Used for autocomplete fields, no permissions required
        limit = 10
        objects = self._getObjects(search=env.request.parameters.get("term"))
        return response.PrewikkaResponse([{"value": obj.name, "label": obj.name} for obj in objects[:limit]])


class UserListingAjax(GenericListingAjax):
    _link = "UserSettings.edit"
    _title = N_("Edit user %s")
    _type = "users"

    @staticmethod
    def _getPermissions(login, ignore_group=False):
        return env.auth.get_user_permissions(login, ignore_group)

    @staticmethod
    def _getObjects(search=None):
        return env.auth.get_user_list(search)

    @view.route("/settings/users/search")
    def search(self):
        return GenericListingAjax.search(self)

    @view.route("/settings/users/delete", methods=["POST"])
    def delete(self):
        if not env.request.user.has("USER_MANAGEMENT"):
            raise error.PrewikkaUserError(N_("Permission Denied"), N_("Access denied to users modification"), log_priority=log.WARNING)

        for obj in env.request.parameters.getlist("id"):
            usergroup.User(userid=obj).delete()

    @view.route("/settings/users/list")
    def listing(self):
        return GenericListingAjax.listing(self)


class GroupListingAjax(GenericListingAjax):
    _link = "GroupSettings.edit"
    _title = N_("Edit group %s")
    _type = "groups"

    @staticmethod
    def _getPermissions(group):
        return env.auth.get_group_permissions(group)

    @staticmethod
    def _getObjects(search=None):
        return env.auth.get_group_list(search)

    @view.route("/settings/groups/search")
    def search(self):
        return GenericListingAjax.search(self)

    @view.route("/settings/groups/delete", methods=["POST"])
    def delete(self):
        if not env.request.user.has("GROUP_MANAGEMENT"):
            raise error.PrewikkaUserError(N_("Permission Denied"), N_("Access denied to groups modification"), log_priority=log.WARNING)

        for obj in env.request.parameters.getlist("id"):
            usergroup.Group(groupid=obj).delete()

    @view.route("/settings/groups/list")
    def listing(self):
        return GenericListingAjax.listing(self)


class SettingsCommon(view.View):
    plugin_htdocs = (("usermanagement", pkg_resources.resource_filename(__name__, 'htdocs')),)
    _template = template.PrewikkaTemplate(__name__, "templates/usersettings.mak")

    def log_property_list_change(self, type, user, orig_list, new_list):
        orig_set = set(orig_list)
        new_set = set(new_list)
        added_set = new_set - orig_set
        deleted_set = orig_set - new_set
        if added_set:
            env.log.info("Added %s (%s) for %s %s" % (type, ", ".join(text_type(i) for i in added_set), self._type, user.name))

        if deleted_set:
            env.log.info("Deleted %s (%s) for %s %s" % (type, ", ".join(text_type(i) for i in deleted_set), self._type, user.name))

    def _get_inactive_permissions(self, old_permissions):
        """Retrieve permissions that have been set previously, but are inactive"""
        inactive_permissions = usergroup.ALL_PERMISSIONS - usergroup.ACTIVE_PERMISSIONS
        return old_permissions & inactive_permissions

    def _make_permissions_from_parameters(self, old_permissions):
        permissions = usergroup.ALL_PERMISSIONS & set(env.request.parameters.getlist("permissions"))
        return permissions | self._get_inactive_permissions(old_permissions)

    def _setup_dataset(self, target, curobj=None):
        dset = self._template.dataset()

        dset["type"] = self._type
        dset["object"] = curobj
        dset["extra_content"] = []
        dset["email"] = ""
        dset["fullname"] = ""
        dset["ask_current_password"] = False
        dset["target"] = target
        dset["timezone"] = env.config.general.default_timezone
        dset["language"] = env.config.general.default_locale
        dset["user_theme"] = env.config.general.default_theme

        dset["can_manage_group_members"] = env.auth.can_manage_group_members()
        dset["member_list"] = []
        dset["object_list"] = []
        dset["extra_content"] = []

        # Group management
        if dset["can_manage_group_members"]:
            dset["object_list"] = [''] + self._getObjects()

        if curobj:
            dset["member_list"] = self._getMembers(curobj)

        dset["permissions"] = []
        for perm in sorted(usergroup.ACTIVE_PERMISSIONS):
            dset["permissions"] += [(perm, False, False)]

        return dset


#
# Theses classes handle drawing the user/group creating dialog (empty settings)
# On validation, (User|Group)SettingsAdd view are called
#
class UserSettings(SettingsCommon):
    _type = "User"

    def _getObjects(self):
        return env.auth.get_group_list()

    def _getMembers(self, obj):
        return env.auth.get_member_of(obj)

    @view.route("/settings/users/<path:name>/save", methods=["POST"])
    @use_transaction
    def save(self, name):
        user = usergroup.User(name)
        modify_self = env.request.user == user

        if not env.auth.has_user(user):
            raise error.PrewikkaUserError(N_("Invalid user"), N_("Specified user does not exist"), log_priority=log.WARNING)

        if name != env.request.user.name and not env.request.user.has("USER_MANAGEMENT"):
            raise error.PrewikkaUserError(N_("Permission Denied"), N_("Cannot modify other users settings"), log_priority=log.WARNING)

        if not env.request.parameters["language"] in localization.get_languages():
            raise error.PrewikkaUserError(N_("Invalid Language"), N_("Specified language does not exist"), log_priority=log.WARNING)

        if not env.request.parameters["timezone"] in localization.get_timezones():
            raise error.PrewikkaUserError(N_("Invalid Timezone"), N_("Specified timezone does not exist"), log_priority=log.WARNING)

        if "password_new" in env.request.parameters and env.request.parameters["password_new"] != env.request.parameters.get("password_new_confirmation"):
            raise error.PrewikkaUserError(N_("Password error"), N_("Password mismatch"))

        reload_type = 0

        for param, reload in (("fullname", "none"), ("email", "none"), ("timezone", "view"), ("theme", "window"), ("language", "window")):
            value = env.request.parameters.get(param)
            if value != user.get_property(param):
                if value:
                    user.set_property(param, value)
                else:
                    user.del_property(param)

                if modify_self:
                    reload_type = max(reload_type, ReloadEnum[reload])

        list(hookmanager.trigger("HOOK_USERMANAGEMENT_USER_MODIFY", user))

        if env.request.user.has("USER_MANAGEMENT") and env.auth.can_manage_permissions():
            permissions = self._make_permissions_from_parameters(user.permissions)

            if permissions != set(user.permissions):
                old_perms = set(env.auth.get_user_permissions(user, ignore_group=True)).difference(env.auth.get_user_permissions_from_groups(user))
                user.permissions = permissions
                self.log_property_list_change("permissions", user, old_perms, permissions)
                reload_type = max(ReloadEnum["window"] if modify_self else ReloadEnum[".commonlisting"], reload_type)

            # Group memberships
            if env.auth.can_manage_group_members():
                groups = set(usergroup.Group(i) for i in env.request.parameters.getlist("member_object"))
                if groups != set(env.auth.get_member_of(user)):
                    self.log_property_list_change("groups", user, env.auth.get_member_of(user), groups)
                    env.auth.set_member_of(user, groups)
                    reload_type = max(ReloadEnum["window"] if modify_self else ReloadEnum[".commonlisting"], reload_type)

        if "password_new" in env.request.parameters:
            if modify_self:
                try:
                    env.auth.authenticate(name, env.request.parameters.get("password_current", ""))
                except auth.AuthError:
                    raise error.PrewikkaUserError(N_("Password error"), N_("Invalid password specified"))

            env.auth.set_password(user, env.request.parameters["password_new"])

        user.sync_properties()

        if reload_type > ReloadEnum["none"]:
            return response.PrewikkaResponse({"type": "reload", "target": reload_type.name})

    @view.route("/settings/users/create", methods=["POST"], permissions=["USER_MANAGEMENT"])
    @use_transaction
    def create(self):
        login = env.request.parameters.get("name")
        if not login:
            raise error.PrewikkaUserError(N_("Could not create user"), N_("Username required"))

        if login.startswith("/"):
            raise error.PrewikkaUserError(N_("Could not create user"), N_("Username cannot start with a slash"))

        user = usergroup.User(login)
        if env.auth.has_user(user):
            raise error.PrewikkaUserError(N_("Could not create user"), N_("User %s already exists", login))

        user.create()
        self.save(login)
        return response.PrewikkaResponse({"type": "reload", "target": ".commonlisting"})

    @view.route("/settings/my_account", menu=(N_("Preferences"), N_("My account")), help="#myaccount")
    def my_account(self):
        return self.edit(env.request.user.name, widget=False)

    @view.route("/settings/users/edit")
    @view.route("/settings/users/<path:name>/edit")
    def edit(self, name=None, widget=True):
        user = None
        user_permissions = []
        group_permissions = []

        if not name:
            target = url_for(".create")
        else:
            user = usergroup.User(name)

            if not env.auth.has_user(user):
                raise error.PrewikkaUserError(_("Invalid User"), N_("Requested user '%s' does not exist", user))

            if user != env.request.user and not env.request.user.has("USER_MANAGEMENT"):
                raise error.PrewikkaUserError(_("Permission Denied"), N_("Access denied to other users settings"), log_priority=log.WARNING)

            target = url_for(".save", name=name)

        dset = self._setup_dataset(target, user)
        if user:
            dset["fullname"] = user.get_property("fullname")
            dset["email"] = user.get_property("email")
            dset["timezone"] = user.get_property("timezone", default=env.config.general.default_timezone)
            dset["language"] = user.get_property("language", default=env.config.general.default_locale)
            dset["user_theme"] = user.get_property("theme", default=env.config.general.default_theme)
            user_permissions = env.auth.get_user_permissions(user, ignore_group=True)
            group_permissions = env.auth.get_user_permissions_from_groups(user)

        dset["widget"] = widget
        dset["ask_current_password"] = (user == env.request.user)

        dset["permissions"] = []
        for perm in sorted(usergroup.ACTIVE_PERMISSIONS):
            dset["permissions"].append((perm, perm in user_permissions, perm in group_permissions))

        dset["extra_content"] = filter(None, hookmanager.trigger("HOOK_USERMANAGEMENT_EXTRA_CONTENT", user, "user"))

        return dset.render()


class GroupSettings(SettingsCommon):
    _type = "Group"

    def _getObjects(self):
        return env.auth.get_user_list()

    def _getMembers(self, obj):
        return env.auth.get_group_members(obj)

    @view.route("/settings/groups/<path:name>/save", methods=["POST"], permissions=["GROUP_MANAGEMENT"])
    def save(self, name):
        group = usergroup.Group(name)
        list(hookmanager.trigger("HOOK_GROUPMANAGEMENT_GROUP_MODIFY", group))

        old_permissions = env.auth.get_group_permissions(group)
        permissions = self._make_permissions_from_parameters(old_permissions)

        self.log_property_list_change("permissions", group, old_permissions, permissions)

        env.auth.set_group_permissions(group, permissions)
        if env.auth.is_member_of(group, env.request.user):
            env.request.user.permissions = env.auth.get_user_permissions(env.request.user)

        # Group memberships
        if env.auth.can_manage_group_members():
            users = set(usergroup.User(i) for i in env.request.parameters.getlist("member_object"))
            self.log_property_list_change("users", group, env.auth.get_group_members(group), users)
            env.auth.set_group_members(group, users)

        return response.PrewikkaResponse({"type": "reload", "target": ".commonlisting"})

    @view.route("/settings/groups/<path:name>/edit", permissions=["GROUP_MANAGEMENT"])
    @view.route("/settings/groups/edit", permissions=["GROUP_MANAGEMENT"])
    def edit(self, name=None, widget=True):
        group = None

        if not name:
            target = url_for(".create")
        else:
            group = usergroup.Group(name)
            target = url_for(".save", name=name)

        dset = self._setup_dataset(target, group)
        if name:
            if not env.request.user.has("GROUP_MANAGEMENT"):
                raise error.PrewikkaUserError(_("Permission Denied"), N_("Access denied to group settings"), log_priority=log.WARNING)

            permissions = env.auth.get_group_permissions(group)

            dset["permissions"] = []
            for perm in sorted(usergroup.ACTIVE_PERMISSIONS):
                dset["permissions"].append((perm, perm in permissions, False))

        dset["widget"] = widget
        dset["extra_content"] = filter(None, hookmanager.trigger("HOOK_GROUPMANAGEMENT_EXTRA_CONTENT", group, "group"))

        return dset.render()

    @view.route("/settings/groups/create", methods=["POST"], permissions=["GROUP_MANAGEMENT"])
    def create(self):
        group_name = env.request.parameters.get("name")
        if not group_name:
            raise error.PrewikkaUserError(N_("Could not create group"), N_("No group name provided"))

        if group_name.startswith("/"):
            raise error.PrewikkaUserError(N_("Could not create group"), N_("Group name cannot start with a slash"))

        group = usergroup.Group(group_name)
        if env.auth.has_group(group):
            raise error.PrewikkaUserError(N_("Could not create group"), N_("Group %s already exists", group_name))

        group.create()
        return self.save(group_name)
