# Copyright (C) 2007-2016 CS-SI. All Rights Reserved.
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

from prewikka import auth, session, usergroup, version


class AnonymousSession(auth.Auth, session.Session):
    plugin_name = "Anonymous authentication"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Anonymous authentication")

    autologin = True

    def __init__(self, config):
        auth.Auth.__init__(self, config)
        session.Session.__init__(self, config)

    def getUserPermissions(self, user, ignore_group=False):
        return usergroup.ALL_PERMISSIONS

    def get_user_info(self, request):
        return session.SessionUserInfo("anonymous", None)

    def getUserList(self, search=None):
        return [ usergroup.User("anonymous") ]

    def hasUser(self, other):
        return usergroup.User("anonymous")

    def authenticate(self, login, password="", no_password_check=False):
        return usergroup.User("anonymous")
