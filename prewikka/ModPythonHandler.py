# Copyright (C) 2005-2014 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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

from prewikka import Core, Request, localization
from mod_python import apache, util, Cookie

class ModPythonRequest(Request.Request):
    def init(self, req):
        self._req = req

        Request.Request.init(self)

        # Copy headers in input_headers to share headers between modpython and internal http server
        self.input_headers = req.headers_in

        fs = util.FieldStorage(req)
        for key in fs.keys():
            self.arguments[key] = fs[key]

    def write(self, data):
        self._req.write(data)

    def sendHeader(self, name, value):
        self._req.headers_out[name] = value

    def endHeaders(self):
        if self._req.headers_out.has_key("Content-type"):
            self._req.content_type = self._req.headers_out["Content-type"]
 
        self._req.send_http_header()

    def addCookie(self, param, value, expires):
        c = Cookie.Cookie(param, value)
        Cookie.add_cookie(self._req, c, expires)

    def getRemoteUser(self):
        self._req.get_basic_auth_pw()

        user = self._req.user
        if user:
            user.strip()

        return user

    def getQueryString(self):
        return self._req.unparsed_uri

    def getCookieString(self):
        return self._req.headers_in.get('cookie', '')

    def getReferer(self):
        return self._req.headers_in.get('Referer', '')

    def getClientAddr(self):
        return self._req.get_remote_host(apache.REMOTE_NOLOOKUP)


def handler(req):
    options = req.get_options()
    request = ModPythonRequest()

    if "PrewikkaConfig" in options:
        config = options["PrewikkaConfig"]
    else:
        config = None

    core = Core.get_core_from_config(config, threaded=True)

    request.init(req)
    core.process(request)

    return apache.OK
