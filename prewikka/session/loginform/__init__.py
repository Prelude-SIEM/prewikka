# Copyright (C) 2013-2020 CS-SI. All Rights Reserved.
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

""" Login/password authentication module """

from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources

from prewikka import session, template, version


class LoginFormSession(session.Session):
    plugin_name = "Login authentication"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Login/Password authentication")
    plugin_htdocs = (("loginform", pkg_resources.resource_filename(__name__, 'htdocs')),)

    template = template.PrewikkaTemplate(__name__, 'templates/loginform.mak')

    def get_user_info(self, request):
        login = request.arguments.pop("_login", None)
        if not login:
            return None

        return session.SessionUserInfo(login, request.arguments.pop("_password", ""))

    def logout(self, request):
        return session.Session.logout(self, request)

    def get_default_auth(self):
        return "dbauth"
