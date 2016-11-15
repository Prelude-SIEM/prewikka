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

from __future__ import absolute_import, division, print_function

import sys
import urllib
import wsgiref.headers
import wsgiref.util

from prewikka import main, utils
from prewikka.web import request

if sys.version_info >= (3,0):
    Py3 = True
    import urllib.parse
else:
    Py3 = False
    import urlparse


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
    def __init__(self, core, environ, start_response):
        request.Request.__init__(self)
        self._headers = None

        self._environ = environ
        self._start_response = start_response
        self.method = environ['REQUEST_METHOD']

        self.path = environ["PATH_INFO"]
        request.Request.init(self, core)

        if self.method != 'POST':
            qs = self._environ.get('QUERY_STRING')
        else:
            qs = self.body = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
            if Py3:
                qs = self.body = qs.decode()

        if Py3:
            self.arguments = urllib.parse.parse_qs(qs)
        else:
            self.arguments = {}
            for k, v in urlparse.parse_qsl(qs):
                self.arguments.setdefault(k.decode("utf8"), []).append(v.decode("utf8"))

        for name, value in self.arguments.items():
            self.arguments[name] = (len(value) == 1) and value[0] or value

        if self._environ.get("HTTP_X_REQUESTED_WITH", "") == "XMLHttpRequest":
            self.is_xhr = True

        # Force request type when client wait explicitly for "text/event-stream"
        if self._environ.get("HTTP_ACCEPT", "text/html") == "text/event-stream":
            self.is_stream = True

    def write(self, data):
        self._write(data)

    def send_headers(self, headers=None, code=200, status_text=None):
        if sys.version_info[0] >= 3:
            headers = list(headers)
        else:
            headers = [ (k.encode("ISO-8859-1"), v.encode("ISO-8859-1")) for k, v in headers ]

        if self._output_cookie:
            headers += [("Set-Cookie", c.OutputString()) for c in self._output_cookie.values()]

        if not status_text:
            status_text = defined_status.get(code, "Unknown")

        self._write = self._start_response("%d %s" % (code, status_text or ""), headers)

    def get_cookie(self):
        return self._environ.get('HTTP_COOKIE', '')

    def get_remote_addr(self):
        return self._environ.get('REMOTE_ADDR')

    def get_remote_port(self):
        return int(self._environ.get('REMOTE_PORT', 0))

    def get_query_string(self):
        return self._environ.get('QUERY_STRING')

    def get_baseurl(self):
        return (env.config.general.reverse_path or self._environ["SCRIPT_NAME"]) + "/"

    def get_raw_uri(self, include_qs=False):
        return wsgiref.util.request_uri(self._environ, include_query=include_qs)

    @property
    def headers(self):
        if self._headers is not None:
            return self._headers

        self._headers = {}
        for key, value in self._environ.items():
            if key.find("HTTP_") == -1:
                continue

            self._headers[key[5:].replace("_", "-").lower()] = value

        return self._headers


def application(environ, start_response):
        # Check whether the URL got a trailing "/", if not perform a redirect
        if not environ["PATH_INFO"]:
            start_response('301 Redirect', [('Location', environ['SCRIPT_NAME'] + "/"),])

        core = main.get_core_from_config(environ.get("PREWIKKA_CONFIG", None))

        core.process(WSGIRequest(core, environ, start_response))
        return []
