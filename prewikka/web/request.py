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

from __future__ import absolute_import, division, print_function

import abc
import sys

from prewikka import error
from prewikka.response import PrewikkaDirectResponse, PrewikkaResponse

if sys.version_info >= (3, 0):
    from http import cookies
else:
    import Cookie as cookies


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


class Request(object):
    def __init__(self, path):
        self.path = path
        self.is_xhr = False
        self.is_stream = False
        self.body = None
        self.arguments = {}
        self._buffer = None
        self._output_cookie = None

        self.path_elements = path.strip('/').split("/")

        cookie = cookies.SimpleCookie(self.get_cookie())
        self.input_cookie = dict(cookie.items())

    def add_cookie(self, param, value, expires, path="/"):
        if not self._output_cookie:
            self._output_cookie = cookies.SimpleCookie()

        if sys.version_info < (3, 0):
            param = param.encode("ascii")
            value = value.encode("utf8")

        self._output_cookie[param] = value
        self._output_cookie[param]["expires"] = expires
        if path:
            self._output_cookie[param]["path"] = path

    def delete_cookie(self, param):
        self.add_cookie(param, "deleted", 0)

    def send_stream(self, data, event=None, evid=None, retry=None, sync=False):
        if self._buffer is None:
            self.is_stream = True
            self._buffer = BufferedWriter(self.write)
            self.write = self._buffer.write

            self.send_headers([("Content-Type", "text/event-stream")])

            if retry:
                self._buffer.write("retry: %d\n" % retry)

        # Join is used in place of concatenation / formatting, because we
        # prefer performance over readability in this place
        if event:
            self._buffer.write("".join(["event: ", event.encode("utf8"), "\n"]))

        if data:
            self._buffer.write("".join(["data: ", data.encode("utf8"), "\n\n"]))

        if sync:
            self._buffer.flush()

    def send_response(self, response, code=200, status_text=None):
        """Send a PrewikkaResponse response."""

        if not isinstance(response, PrewikkaResponse):
            response = PrewikkaDirectResponse(response, code=code, status_text=status_text)

        if self.is_stream:
            if isinstance(response.data, error.PrewikkaError):
                self.send_stream(response.content(), event="error")

            self._buffer.flush()
        else:
            response.write(self)

    @abc.abstractmethod
    def send_headers(self, headers=[], code=200, status_text=None):
        pass

    @abc.abstractmethod
    def get_baseurl(self):
        pass

    @abc.abstractmethod
    def get_raw_uri(self, include_qs=False):
        pass

    @abc.abstractmethod
    def get_remote_addr(self):
        pass

    @abc.abstractmethod
    def get_remote_port(self):
        pass

    @abc.abstractmethod
    def get_cookie(self):
        pass

    @abc.abstractmethod
    def write(self, data):
        pass
