# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

from prewikka import env, hookmanager, log, pluginmanager, usergroup
from prewikka.error import NotImplementedError, PrewikkaUserError


class AuthError(PrewikkaUserError):
    def __init__(self, session, message=N_("Authentication failed"), log_priority=log.ERROR, log_user=None):
        PrewikkaUserError.__init__(self, None, message, log_priority=log_priority, log_user=log_user, template=session.template)


class _AuthUser(object):
    def canCreateUser(self):
        return "createUser" in self.__class__.__dict__

    def canDeleteUser(self):
        return "deleteUser" in self.__class__.__dict__

    def canSetPassword(self):
        return "setPassword" in self.__class__.__dict__

    def canManagePermissions(self):
        return self.__class__.setUserPermissions != _AuthUser.setUserPermissions

    def createUser(self, user):
        list(hookmanager.trigger("HOOK_USER_CREATE", user))

    def deleteUser(self, user):
        list(hookmanager.trigger("HOOK_USER_DELETE", user))
        env.db.del_properties(user)

    @abc.abstractmethod
    def getUserList(self, search=None):
        return []

    @abc.abstractmethod
    def getUserByID(self, id_):
        raise NotImplementedError

    @abc.abstractmethod
    def hasUser(self, user):
        raise NotImplementedError

    @abc.abstractmethod
    def getUserPermissions(self, login, ignore_group=False):
        return []

    @abc.abstractmethod
    def getUserPermissionsFromGroups(self, login):
        return []

    @abc.abstractmethod
    def setUserPermissions(self, login, permissions):
        raise NotImplementedError


class _AuthGroup(object):
    def canHandleGroups(self):
        return self.__class__.getGroupByID != _AuthGroup.getGroupByID

    def canCreateGroup(self):
        return "createGroup" in self.__class__.__dict__

    def canDeleteGroup(self):
        return "deleteGroup" in self.__class__.__dict__

    def canManageGroupMembers(self):
        return self.__class__.setGroupMembers != _AuthGroup.setGroupMembers

    def canManageGroupPermissions(self):
        return self.__class__.setGroupPermissions != _AuthGroup.setGroupPermissions

    def getGroupList(self, search=None):
        return []

    def getGroupByID(self, id_):
        raise NotImplementedError

    def createGroup(self, group):
        list(hookmanager.trigger("HOOK_GROUP_CREATE", group))

    def deleteGroup(self, group):
        list(hookmanager.trigger("HOOK_GROUP_DELETE", group))

    def setGroupPermissions(self, group, permissions):
        raise NotImplementedError

    def getGroupPermissions(self, group):
        return []

    def setGroupMembers(self, group, logins):
        raise NotImplementedError

    def getGroupMembers(self, group):
        return []

    def setMemberOf(self, login, groups):
        raise NotImplementedError

    def getMemberOf(self, login):
        return []

    def isMemberOf(self, group, login):
        raise NotImplementedError

    def hasGroup(self, group):
        raise NotImplementedError


class Auth(pluginmanager.PluginBase, _AuthUser, _AuthGroup):
    __metaclass__ = abc.ABCMeta
    plugin_mandatory = True

    def __init__(self, config):
        pluginmanager.PluginBase.__init__(self)
        _AuthUser.__init__(self)
        _AuthGroup.__init__(self)

    def init(self, config):
        pass

    def authenticate(self, login, password="", no_password_check=False):
        raise NotImplementedError

    def getDefaultSession(self):
        raise NotImplementedError
