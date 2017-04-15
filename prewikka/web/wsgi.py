# Copyright (C) 2015-2017 CS-SI. All Rights Reserved.
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

from prewikka import main
from prewikka.web import request

if sys.version_info >= (3, 0):
    Py3 = True
    import urllib.parse
else:
    Py3 = False
    import urlparse


defined_status = {
    200: 'Ok',
    304: 'Not Modified',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    500: 'Internal Server Error',
}


class WSGIRequest(request.Request):

    def _wsgi_get_bytes(self, key, default=None):
        value = self._environ.get(key, default)

        # Under Python 3, non-ASCII values in the WSGI environ are arbitrarily
        # decoded with ISO-8859-1. This is wrong for Prewikka where UTF-8 is the
        # default. Re-encode to recover the original bytestring.
        return value.encode("ISO-8859-1") if Py3 else value

    def _wsgi_get_unicode(self, key, default=None):
        return self._wsgi_get_bytes(key, default).decode("utf8")

    def _wsgi_get_str(self, key, default=None):
        value = self._wsgi_get_bytes(key, default)
        return value.decode("utf8") if Py3 else value

    def __init__(self, environ, start_response):
        self._environ = environ
        self._headers = None
        self._start_response = start_response
        self.method = environ['REQUEST_METHOD']

        request.Request.__init__(self, self._wsgi_get_unicode("PATH_INFO"))

        if self.method != 'POST':
            qs = self._wsgi_get_str("QUERY_STRING")
        else:
            qs = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
            qs = self.body = qs.decode("utf8") if Py3 else qs

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
        return self._wsgi_get_str('HTTP_COOKIE', '')

    def get_remote_addr(self):
        return self._wsgi_get_unicode('REMOTE_ADDR')

    def get_remote_port(self):
        return int(self._environ.get('REMOTE_PORT', 0))

    def get_query_string(self):
        return self._wsgi_get_unicode('QUERY_STRING')

    def get_script_name(self):
        return self._wsgi_get_unicode("SCRIPT_NAME")

    def get_baseurl(self):
        return (env.config.general.reverse_path or self.get_script_name()) + "/"

    def get_uri(self):
        return self.get_script_name() + self.path

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
        core = main.Core.from_config(environ.get("PREWIKKA_CONFIG", None))
        core.process(WSGIRequest(environ, start_response))

        return []
