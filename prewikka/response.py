# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function

import mimetypes
import os
import time
import datetime
import dateutil.parser

from prewikka import compat, template, utils
from prewikka.utils import json


_sentinel = object()

_ADDITIONAL_MIME_TYPES = [("application/vnd.oasis.opendocument.formula-template", ".otf"),
                          ("application/vnd.ms-fontobject", ".eot"),
                          ("image/vnd.microsoft.icon", ".ico"),
                          ("application/font-woff", ".woff"),
                          ("application/font-sfnt", ".ttf"),
                          ("application/json", ".map"),
                          ("font/woff2", ".woff2")]


for mtype, extension in _ADDITIONAL_MIME_TYPES:
    mimetypes.add_type(mtype, extension)


class PrewikkaResponse(object):
    """
        HTML response

        Use this class to render HTML in your view.

        :param data: Data of the response
        :param int code: HTTP response code
        :param str status_text: HTTP response status text

        If the type of data is a dict, it will be cast in a JSON string
    """

    def __init__(self, data=None, headers=_sentinel, code=None, status_text=None):
        self.data = data
        self.code = code or 200
        self.status_text = status_text
        self.ext_content = {}

        if headers is not _sentinel:
            self.headers = headers
        else:
            self.headers = utils.OrderedDict((("Content-Type", "text/html"),
                                              ("Last-Modified", time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())),
                                              ("Expires", "Fri, 01 Jan 1999 00:00:00 GMT"),
                                              ("Cache-control", "no-store, no-cache, must-revalidate"),
                                              ("Cache-control", "post-check=0, pre-check=0"),
                                              ("Pragma", "no-cache")))

    def add_ext_content(self, key, value):
        """Add an extra content to the response (add in XHR request)."""

        self.ext_content[key] = value

    def add_notification(self, message, classname="success", name=None, icon=None, duration=None):
        """Add notification to the return value."""

        self.ext_content.setdefault("notifications", []).append({
            "message": message,
            "classname": classname,
            "name": name,
            "icon": icon,
            "duration": duration
        })

    @staticmethod
    def _is_xhr_embedded_content(obj):
        is_json = hasattr(obj, '__json__')
        if is_json and not isinstance(obj, template.PrewikkaTemplate):
            return False

        return True

    def content(self):
        """Retrieve the HTML content of the response."""
        if env.request.web.is_xhr and self._is_xhr_embedded_content(self.data):
            res = self._with_xhr_layout(self.data)
        else:
            res = self.data

        return self._encode_response(res)

    def _encode_response(self, res):
        if res is None:
            res = ""

        if not isinstance(res, compat.STRING_TYPES):
            self.headers["Content-Type"] = "application/json"
            res = json.dumps(res)

        return res.encode(env.config.general.get("encoding", "utf8"), "xmlcharrefreplace")

    def _with_xhr_layout(self, obj):
        """Position the obj in a dict for XHR response"""

        data = {"type": "html", "content": obj}
        data.update(self.ext_content)

        return data

    def write(self, request):
        content = self.content()

        request.send_headers(self.headers.items(), self.code, self.status_text)
        request.write(content)


class PrewikkaDownloadResponse(PrewikkaResponse):
    """
        File Download Response

        Use this class for download response (pdf, csv, ...).

        :param str data: The inner content of the file, or a file object
        :param str filename: Name for the file to be downloaded
        :param str type: Type of the file as mime type (will try to guess if None)
        :param int size: Size of the data (will be computed automatically if None)
        :param bool inline: Whether to display the downloaded file inline
    """
    def __init__(self, data, filename=None, type=None, size=None, inline=False):
        PrewikkaResponse.__init__(self, data)

        if filename and not type:
            type = mimetypes.guess_type(filename)[0]

        if not type:
            type = "application/octet-stream"

        disposition = "inline" if inline else "attachment"
        if filename:
            disposition += "; filename=\"%s\"" % filename

        self._is_file = not(isinstance(self.data, text_type))
        if not size:
            if self._is_file:
                size = os.fstat(self.data.fileno()).st_size
            else:
                size = len(data)

        self.headers.update((
            ("Content-Type", type),
            ("Content-Length", str(size)),
            ("Content-Disposition", disposition),
            ("Pragma", "public"),
            ("Cache-Control", "max-age=0")
        ))

    def write(self, request):
        request.send_headers(self.headers.items(), self.code, self.status_text)

        if not self._is_file:
            request.write(self.data)
        else:
            for i in iter(lambda: self.data.read(8192), b''):
                request.write(i)


class PrewikkaDirectResponse(PrewikkaResponse):
    """
        Direct HTML response

        Render the directly the data without wrapping it, even on XHR request.
    """

    def content(self):
        return self._encode_response(self.data)


class PrewikkaFileResponse(PrewikkaResponse):
    """
        Static File response
    """
    def __init__(self, path):
        PrewikkaResponse.__init__(self)
        self._path = path

        stat = os.stat(path)
        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        mtime = datetime.datetime.utcfromtimestamp(stat.st_mtime).replace(tzinfo=utils.timeutil.tzutc())

        ims = env.request.web.headers.get("if-modified-since")
        if ims is not None:
            ims = dateutil.parser.parse(ims)
            if mtime <= ims:
                self.code = 304

        self.headers = utils.OrderedDict((('Content-Type', content_type),))

        if self.code != 304:
            self.headers["Content-Length"] = str(stat.st_size)
            self.headers["Expires"] = (mtime + datetime.timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            self.headers["Last-Modified"] = mtime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def write(self, request):
        request.send_headers(self.headers.items(), self.code, self.status_text)
        if self.code == 304:
            return

        with open(self._path, 'rb') as fd:
            for i in iter(lambda: fd.read(8192), b''):
                request.write(i)


class PrewikkaRedirectResponse(PrewikkaResponse):
    """
        Redirect response
    """
    def __init__(self, location, code=302, status_text=None):
        PrewikkaResponse.__init__(self, code=code, status_text=status_text or "%d Redirect" % code)
        self.headers = utils.OrderedDict((('Location', location),))
