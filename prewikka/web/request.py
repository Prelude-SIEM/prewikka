# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
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

import sys, os, os.path, time, copy, Cookie
import mimetypes, urllib, cgi
from prewikka import env, error
from prewikka.response import PrewikkaResponse, PrewikkaDownloadResponse

_ADDITIONAL_MIME_TYPES = [("application/vnd.oasis.opendocument.formula-template", ".otf"),
                          ("application/vnd.ms-fontobject", ".eot"),
                          ("image/vnd.microsoft.icon", ".ico"),
                          ("application/font-woff", ".woff"),
                          ("application/font-sfnt", ".ttf"),
                          ("application/json", ".map"),
                          ("font/woff2", ".woff2")]

for mtype, extension in _ADDITIONAL_MIME_TYPES:
    mimetypes.add_type(mtype, extension)


class BufferedWriter:
        def __init__(self, wcb, buffersize=8192):
                self._wcb = wcb
                self._dlist = []
                self._len = 0
                self._buffersize = buffersize

        def flush(self):
                self._wcb(''.join(self._dlist))
                self._dlist = []
                self._len = 0

        def write(self, data):
                self._dlist.append(data)
                self._len += len(data)

                if self._len >= self._buffersize:
                        self.flush()


class Request:
    path = None

    def init(self, core):
        # all of this should be done in constructor __init__, but the way
        # BaseHTTPServer.BaseHTTPRequestHandler is designed forbid us to do so
        self.is_xhr = False
        self.is_multipart = False
        self.is_stream = False
        self._buffer = None

        self._core = core

        self.arguments = { }
        self.output_headers = [ ("Content-type", "text/html"),
                                ("Last-Modified", time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())),
                                ("Expires", "Fri, 01 Jan 1999 00:00:00 GMT"),
                                ("Cache-control", "no-store, no-cache, must-revalidate"),
                                ("Cache-control", "post-check=0, pre-check=0"),
                                ("Pragma", "no-cache") ]

        cookie = Cookie.SimpleCookie(self.getCookieString())
        self.input_cookie = { }
        for key, value in cookie.items():
            self.input_cookie[key] = value

        self.output_cookie = None

    def addCookie(self, param, value, expires, path="/"):
        if not self.output_cookie:
            self.output_cookie = Cookie.SimpleCookie()

        self.output_cookie[param] = value
        self.output_cookie[param]["expires"] = expires
        if path:
            self.output_cookie[param]["path"] = path


    def deleteCookie(self, param):
        self.addCookie(param, "deleted", 0)

    def read(self, *args):
        pass

    def write(self, data):
        pass

    def sendHeaders(self, headers=None, code=200, status_text=None):
        if not headers:
            headers = self.output_headers

        if self.output_cookie:
            headers.extend(("Set-Cookie", c.OutputString()) for c in self.output_cookie.values())

        for name, value in headers:
            self.sendHeader(name, value)

        self.endHeaders()

    def sendHeader(self, name, value):
        self.write("%s: %s\r\n" % (name, value))

    def endHeaders(self):
        self.write("\r\n")

    def sendRedirect(self, location, redirect_code=307):
        self.output_headers = [('Location', location)]
        self.sendResponse(None, code=redirect_code, status_text="%d Redirect" % redirect_code)

    def sendStream(self, data, event=None, evid=None, retry=None, sync=False):
        if self._buffer is None:
            self.is_stream = True
            self._buffer = BufferedWriter(self.write)
            self.write = self._buffer.write

            self.sendHeaders([("Content-Type", "text/event-stream")])

            if retry:
                 self._buffer.write("retry: %d\n" % retry)

        # Join is used in place of concatenation / formatting, because we
        # prefer performance over readability in this place
        if event:
                self._buffer.write("".join(["event: ", event, "\n"]))

        if data:
                self._buffer.write("".join(["data: ", data, "\n\n"]))

        if sync:
                self._buffer.flush()

    def sendResponse(self, response, code=200, status_text=None):
        """Send a PrewikkaResponse response."""

        if not response:
            response = PrewikkaResponse()

        if env.request.web.is_stream:
            if isinstance(response, error.PrewikkaUserError):
                env.request.web.sendStream(response.content(), event="error")
                return

            env.request.web.close_stream()

        if response.code:
            code = response.code

        if response.status_text:
            status_text = response.status_text

        if response.force_download:
            self.force_download(response.filename, response.type, response.size)

        env.request.web.sendHeaders(self.output_headers, code, status_text)

        html = response.content()
        if html:
            env.request.web.write(html)

    def force_download(self, filename, type, size):
        """Add file download headers."""

        self.output_headers = [
            ("Content-Type", type),
            ("Content-Disposition", "attachment; filename=%s" % filename),
            ("Pragma", "public"),
            ("Cache-Control", "max-age=0")
        ]
        if size:
            self.output_headers.append(("Content-length", str(size)))

    def close_stream(self):
        """Close the stream."""
        self.sendStream("close", event="close")
        self._buffer.flush()

    def resolveStaticPath(self, fname):
        pathmap = env.htdocs_mapping
        pathkey = fname[1:].split("/")[0]

        mapping = pathmap.get(pathkey, None)
        if not mapping:
           return

        path = os.path.abspath(os.path.join(mapping, urllib.unquote(fname[len(pathkey) + 2:])))
        if not path.startswith(mapping):
                self.sendResponse(None, 403, status_text="Request Forbidden")
                return

        # If the path doesn't exist or is not a regular file return None so that prewikka
        # attempt to resolve a view with the same name as the defined file mapping
        return path if os.path.isfile(path) else None

    def processStatic(self, path, copyfunc):
        try:
                fd = open(path, "r")
        except:
                self.sendResponse(None, 404, status_text="File not found")
                return

        stat = os.fstat(fd.fileno())

        content_type = mimetypes.guess_type(path)[0]
        if not content_type:
            env.log.warning("Serving file with unknown MIME type: %s" % path)
            content_type = "application/octet-stream"

        self.output_headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(stat[6])),
            ('Last-Modified', time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(stat[8])))]

        self.sendHeaders()
        return copyfunc(fd)

    def handleMultipart(self, *args, **kwargs):
        arguments = {}
        fs = cgi.FieldStorage(**kwargs)

        for key in fs.keys():
            # FIXME : remove next part when IE9 support will be dropped
            # Support for jquery-iframe-transport
            if key == "X-Requested-With" and fs[key].value == "IFrame":
                self.is_xhr = True
                continue

            value = fs[key]
            for i, f in enumerate(value if isinstance(value, list) else [value]):
                if f.filename:
                    arguments["%s_data_%d" % (key, i)] = f.value
                    arguments["%s_name_%d" % (key, i)] = f.filename
                else:
                    arguments[key] = f.value

        self.is_multipart = True
        return arguments

    def getView(self):
        if not self.path:
                return "/"

        return self.path

    def getViewElements(self):
        return self.getView().strip("/").split("/")

    def getBaseURL(self):
        return env.config.general.reverse_path + "/"

    def getQueryString(self):
        pass

    def getHeader(self, name):
        pass

    def getClientAddr(self):
        pass

    def getClientPort(self):
        pass

    def getServerAddr(self):
        pass

    def getServerPort(self):
        pass

    def getUserAgent(self):
        pass

    def getMethod(self):
        pass

    def getURI(self):
        pass
