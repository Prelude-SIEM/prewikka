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

import json

from prewikka import env, compat, utils, template


class PrewikkaResponse(object):
    """
        HTML response

        Use this class to render HTML in your view.

        :param data: Data of the response
        :param int code: HTTP response code
        :param str status_text: HTTP response status text

        If the type of data is a dict, it will be cast in a JSON string
    """

    def __init__(self, data=None, code=None, status_text=None):
        self.data = data
        self.force_download = False
        self.code = code
        self.status_text = status_text
        self.ext_content = {}

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

    def _is_xhr_embedded_content(self, obj):
        is_json = hasattr(self.data, '__json__')
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
            res = json.dumps(res, cls=utils.PrewikkaJSONEncoder)

        return res.encode(env.config.general.get("encoding", "utf8"), "xmlcharrefreplace")

    def _with_xhr_layout(self, obj):
        """Position the obj in a dict for XHR response"""

        data = {"content": obj}
        data.update(self.ext_content)

        return data


class PrewikkaDownloadResponse(PrewikkaResponse):
    """
        File Download Response

        Use this class for download response (pdf, csv, ...).

        :param str data: The inner content of the file
        :param str filename: Filename of the file
        :param str type: Type of the file as mime type
        :param int size: Size of the data (default to len(data))
    """

    def __init__(self, data, filename, type="application/force-download", size=None):
        PrewikkaResponse.__init__(self, data)
        self.force_download = True
        self.filename = filename
        self.type = type
        self.size = size or len(data)

    def content(self):
        return self.data


class PrewikkaDirectResponse(PrewikkaResponse):
    """
        Direct HTML response

        Render the directly the data without wrapping it, even on XHR request.
    """

    def content(self):
        return self._encode_response(self.data)

