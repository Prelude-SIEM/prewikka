# Copyright (C) 2005 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.

from prewikka import Core, Request, localization
from mod_python import apache, util, Cookie

class ModPythonRequest(Request.Request):
    def init(self, req):
    	self._req = req

	Request.Request.init(self)

	fs = util.FieldStorage(req)
	for key in fs.keys():
            self.arguments[key] = fs[key]
       
    def write(self, data):
        self._req.write(data)

    def sendHeader(self, name, value):
        self._req.headers_out[name] = value
         
    def endHeaders(self):
    	pass

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
    req.content_type = 'text/html'
    req.send_http_header()

    core.process(request)

    return apache.OK
