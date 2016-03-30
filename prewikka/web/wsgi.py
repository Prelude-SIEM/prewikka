# Copyright (C) 2015-2016 CS-SI. All Rights Reserved.
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

import cgi
from prewikka.web import request
from prewikka import main, env

defined_status = {
        200: 'OK',
        400: 'BAD REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT FOUND',
        405: 'METHOD NOT ALLOWED',
        500: 'INTERNAL SERVER ERROR',
}

class WSGIRequest(request.Request):
    def init(self, core, environ, start_response):
        self._environ = environ
        self._start_response = start_response

        request.Request.init(self, core)

        if self.getMethod() != 'POST':
            self.arguments = cgi.parse_qs(self.getQueryString())
        else:
            if self._environ.get("CONTENT_TYPE", "").startswith("multipart/form-data"):
                self.arguments = self.handleMultipart(fp=environ['wsgi.input'], environ=environ)
            else:
                self.arguments = cgi.parse_qs(environ['wsgi.input'].read())

        for name, value in self.arguments.items():
            self.arguments[name] = (len(value) == 1) and value[0] or value

        if self._environ.get("HTTP_X_REQUESTED_WITH", "") == "XMLHttpRequest":
            self.is_xhr = True

        # Force request type when client wait explicitly for "text/event-stream"
        if self._environ.get("HTTP_ACCEPT", "text/html") == "text/event-stream":
            self.is_stream = True


    def getBaseURL(self):
        return (env.config.reverse_path or self._environ["SCRIPT_NAME"]) + "/"

    def getMethod(self):
        return self._environ['REQUEST_METHOD']

    def write(self, data):
        self._write(data)

    def sendHeaders(self, code=200, status_text=None):
        if self.output_cookie:
            self.output_headers.extend(("Set-Cookie", c.OutputString()) for c in self.output_cookie.values())

        if not status_text:
            status_text = defined_status.get(code, "Unknown")

        self._write = self._start_response("%d %s" % (code, status_text), self.output_headers)

    def getHeader(self, name):
        return self._environ[name]

    def getQueryString(self):
        return self._environ.get('QUERY_STRING')

    def getCookieString(self):
        return self._environ.get('HTTP_COOKIE', '')

    def getReferer(self):
        return self._req.headers_in.get('HTTP_REFERER', '')

    def getClientAddr(self):
        return self._environ.get('REMOTE_ADDR')

    def getClientPort(self):
        return int(self._environ.get('REMOTE_PORT'))


def application(environ, start_response):
        req = WSGIRequest()

        core = main.get_core_from_config(environ.get("PREWIKKA_CONFIG", None))
        req.init(core, environ, start_response)

        # Check whether the URL got a trailing "/", if not perform a redirect
        if not environ["PATH_INFO"]:
                start_response('301 Redirect', [('Location', environ['SCRIPT_NAME'] + "/"),])

        path = req.resolveStaticPath(environ["PATH_INFO"])
        if path:
                return req.processStatic(path, lambda fd: fd) or []
        else:
                req.path = environ["PATH_INFO"]
                core.process(req)

        return []
