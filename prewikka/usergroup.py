# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

from __future__ import absolute_import, division, print_function, unicode_literals

import abc
import hashlib

from prewikka import compat, error, localization, log, utils
from prewikka.utils import cache, json

ADMIN_LOGIN = "admin"
_NAMEID_TBL = {}


class PermissionDeniedError(error.PrewikkaUserError):
    def __init__(self, permissions, view=None):
        if isinstance(permissions, compat.STRING_TYPES):
            permissions = [permissions]

        if view and permissions:
            msg = N_("Access to view '%(view)s' forbidden. Required permissions: %(permissions)s",
                     {"view": view, "permissions": ", ".join(permissions)})

        elif view:
            msg = N_("Access to view '%s' forbidden", view)

        else:
            msg = N_("Required permissions: %s", ", ".join(permissions))

        error.PrewikkaUserError.__init__(self, N_("Permission Denied"), msg, log_priority=log.WARNING)


def permissions_required(permissions):
    ALL_PERMISSIONS.declare(permissions)

    def has_permissions(func):
        def wrapper(*args, **kwargs):
            if env.request.user:
                env.request.user.check(permissions)
            return func(*args, **kwargs)
        return wrapper
    return has_permissions


class Permissions(set):
    """ List of all the permissions available """

    def declare(self, permission):
        """Add the permission to the set if it is not already declared"""
        if isinstance(permission, compat.STRING_TYPES):
            self.add(permission)
        else:
            self.update(permission)


ALL_PERMISSIONS = Permissions()


class NameID(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name=None, nameid=None):
        assert(name or nameid)

        self._id = nameid
        self._name = name

    @property
    def id(self):
        if self._id is None:
            self._id = self._name2id(self._name)

        return self._id

    @property
    def name(self):
        if self._name is None:
            self._name = self._id2name(self._id)

        return self._name

    @abc.abstractmethod
    def _id2name(self, id):
        pass

    def _name2id(self, name):
        md5 = _NAMEID_TBL.get(name)
        if md5:
            return md5

        md5 = _NAMEID_TBL[name] = hashlib.md5(name.encode("utf8")).hexdigest()
        return md5

    def __eq__(self, other):
        if not other:
            return False

        return self.id == other.id

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return int(self.id, 16)

    def __str__(self):
        return self.name


class Group(NameID):
    def __init__(self, name=None, groupid=None):
        NameID.__init__(self, name, groupid)

    def _id2name(self, id):
        return env.auth.getGroupByID(id).name


def _sync_if_needed(func):
    def inner(self, *args, **kwargs):
        if self._properties_state:
            return func(self, *args, **kwargs)

        self.begin_properties_change()
        ret = func(self, *args, **kwargs)
        self.commit_properties_change()

        return ret

    return inner



class User(NameID):
    __sentinel = object()
    __PROPERTIES_STATE_NONE  = 0x00
    __PROPERTIES_STATE_BEGIN = 0x01
    __PROPERTIES_STATE_DIRTY = 0x02

    def __init__(self, login=None, userid=None):
        NameID.__init__(self, login, userid)
        self._properties_state = self.__PROPERTIES_STATE_NONE

    def _id2name(self, id):
        return env.auth.getUserByID(id).name

    @cache.request_memoize_property("user_permissions")
    def permissions(self):
        return set(env.auth.getUserPermissions(self))

    @permissions.setter
    def permissions(self, permissions):
        env.auth.setUserPermissions(self, permissions)

    def _permissions(self, permissions):
        self.permissions  # make sure the cache has been created
        env.request.cache.user_permissions._set((self,), set(permissions))

    # Support access to _permissions to modify object permission without backend modification.
    _permissions = property(permissions, _permissions)

    @cache.request_memoize_property("user_configuration")
    def configuration(self):
        rows = env.db.query("SELECT config FROM Prewikka_User_Configuration WHERE userid = %s", self.id)
        if rows:
            return json.loads(rows[0][0])

        return {}

    @cache.request_memoize_property("user_timezone")
    def timezone(self):
        return utils.timeutil.timezone(self.get_property("timezone", default=env.config.general.default_timezone))

    def set_locale(self):
        lang = self.get_property("language", default=env.config.general.default_locale)
        if lang:
            localization.setLocale(lang)

    @_sync_if_needed
    def del_property(self, key, view=None):
        view = view or ""

        if not key:
            r = self.configuration.pop(view, None)
        else:
            r = self.configuration.get(view, {}).pop(key, None)

        if r:
            self._properties_state |= self.__PROPERTIES_STATE_DIRTY

    def delete(self):
        env.db.query("DELETE FROM Prewikka_User_Configuration WHERE userid = %s", self.id)

    @_sync_if_needed
    def del_properties(self, view):
        r = self.configuration.pop(view, None)
        if r:
            self._properties_state |= self.__PROPERTIES_STATE_DIRTY

    def del_property_match(self, key, view=None):
        view = view or ""
        viewlist = [view] if view else self.configuration.keys()

        for v in viewlist:
            if v not in self.configuration:
                continue

            for k in self.configuration[v].keys():
                if k.find(key) != -1:
                    self.del_property(k, view=v)

    def get_property_fail(self, key, view=None, default=__sentinel):
        view = self.configuration.get(view or "", {})

        if default is not self.__sentinel:
            return view.get(key, default)

        return view[key]

    def has_property(self, key, view=None):
        return key in self.configuration.get(view or "", {})

    def get_property(self, key, view=None, default=None):
        return self.get_property_fail(key, view or "", default)

    @_sync_if_needed
    def set_property(self, key, value, view=None):
        old = self.configuration.get(view or "", {}).get(key)
        if old != value:
            self._properties_state |= self.__PROPERTIES_STATE_DIRTY

        self.configuration.setdefault(view or "", {})[key] = value

    def begin_properties_change(self):
        self._properties_state = self.__PROPERTIES_STATE_BEGIN

    def commit_properties_change(self):
        if self._properties_state & self.__PROPERTIES_STATE_DIRTY:
            env.db.upsert("Prewikka_User_Configuration", ["userid", "config"], [[self.id, json.dumps(self.configuration)]], pkey=("userid",))

        self._properties_state = self.__PROPERTIES_STATE_NONE

    def has(self, perm):
        if type(perm) in (list, tuple, set):
            return self.permissions.issuperset(perm)

        return perm in self.permissions

    def check(self, perm, view=None):
        if not self.has(perm):
            raise PermissionDeniedError(perm, view)
