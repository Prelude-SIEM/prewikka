# Copyright (C) 2004-2019 CS-SI. All Rights Reserved.
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

from prewikka import log, pluginmanager
from prewikka.error import NotImplementedError, PrewikkaUserError


class AuthError(PrewikkaUserError):
    def __init__(self, session, message=N_("Authentication failed"), log_priority=log.ERROR, log_user=None):
        PrewikkaUserError.__init__(self, None, message, log_priority=log_priority, log_user=log_user, template=session.template)


class _AuthUser(object):
    def can_create_user(self):
        return self.__class__.create_user != _AuthUser.create_user

    def can_delete_user(self):
        return self.__class__.delete_user != _AuthUser.delete_user

    def can_set_password(self):
        return self.__class__.set_password != _AuthUser.set_password

    def can_manage_permissions(self):
        return self.__class__.set_user_permissions != _AuthUser.set_user_permissions

    @abc.abstractmethod
    def create_user(self, user):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_user(self, user):
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_list(self, search=None):
        return []

    @abc.abstractmethod
    def get_user_by_id(self, id_):
        raise NotImplementedError

    @abc.abstractmethod
    def has_user(self, user):
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_permissions(self, user, ignore_group=False):
        return []

    @abc.abstractmethod
    def get_user_permissions_from_groups(self, user):
        return []

    @abc.abstractmethod
    def set_user_permissions(self, user, permissions):
        raise NotImplementedError

    @abc.abstractmethod
    def set_password(self, user, password):
        raise NotImplementedError


class _AuthGroup(object):
    def can_handle_groups(self):
        return self.__class__.get_group_by_id != _AuthGroup.get_group_by_id

    def can_create_group(self):
        return self.__class__.create_group != _AuthGroup.create_group

    def can_delete_group(self):
        return self.__class__.delete_group != _AuthGroup.delete_group

    def can_manage_group_members(self):
        return self.__class__.set_group_members != _AuthGroup.set_group_members

    def can_manage_group_permissions(self):
        return self.__class__.set_group_permissions != _AuthGroup.set_group_permissions

    def get_group_list(self, search=None):
        return []

    def get_group_by_id(self, id_):
        raise NotImplementedError

    @abc.abstractmethod
    def create_group(self, group):
        raise NotImplementedError

    @abc.abstractmethod
    def delete_group(self, group):
        raise NotImplementedError

    def set_group_permissions(self, group, permissions):
        raise NotImplementedError

    def get_group_permissions(self, group):
        return []

    def set_group_members(self, group, users):
        raise NotImplementedError

    def get_group_members(self, group):
        return []

    def set_member_of(self, user, groups):
        raise NotImplementedError

    def get_member_of(self, user):
        return []

    def is_member_of(self, group, user):
        raise NotImplementedError

    def has_group(self, group):
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

    def get_default_session(self):
        raise NotImplementedError
