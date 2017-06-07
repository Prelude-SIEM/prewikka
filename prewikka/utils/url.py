# Copyright (C) 2004-2017 CS-SI. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import base64
import errno
import os.path
import sys
import prelude
import random

from prewikka import siteconfig


if sys.version_info >= (3,0):
    from urllib.parse import quote, unquote, urlsplit, urlunsplit, urlencode as _urlencode
else:
    from urllib import quote, unquote, urlencode as __urlencode
    from urlparse import urlsplit, urlunsplit

    def _convert(d):
        if isinstance(d, (list, tuple)):
            return [_convert(i) for i in d]

        elif isinstance(d, text_type):
            return d.encode("utf8")

        else:
            return d

    def _urlencode(parameters, doseq=False):
        if hasattr(parameters, "items"):
            parameters = parameters.items()

        return __urlencode([(k.encode("utf8"), _convert(v)) for k, v in parameters], doseq)


class mkdownload(object):
    DOWNLOAD_DIRECTORY = os.path.join(siteconfig.data_dir, "download")

    """
        Create a file to be downloaded

        :param str filename: Name of the file as downloaded by the user
        :param str mode: Mode for opening the file (default is 'wb+')
        :param bool user: User who can download the file (default to current user, False or a specific user can be provided).
        :param bool inline: Whether to display the downloaded file inline
    """
    def __init__(self, filename, mode="wb+", user=True, inline=False):
        self.name = filename
        self._id = random.randint(0, 9999999)
        self._dlname = base64.urlsafe_b64encode(filename.encode("utf8"))
        filename = self.get_filename(self._id, self._dlname, user)

        try:
            os.makedirs(os.path.dirname(filename), mode=0o700)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

        self.fd = open(filename, mode)

        self._user = user
        self._inline = inline

    @property
    def href(self):
        user = self._get_user(self._user)
        return "%sdownload%s/%d/%s%s" % (env.request.web.get_baseurl(), "/" + user if user else "", self._id, self._dlname, "/inline" if self._inline else "")

    @classmethod
    def get_filename(cls, id, filename, user=True):
        user = cls._get_user(user)
        if user:
            user = base64.urlsafe_b64encode(user.encode("utf8"))

        return os.path.join(cls.DOWNLOAD_DIRECTORY, user or "", "%d-%s" % (id, filename))

    @staticmethod
    def _get_user(user):
        if user is True:
            return env.request.user.name

        # handle string and User object
        return getattr(user, "name", user or "")

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.fd.close()

    def __getattr__(self, attr):
        return getattr(self.fd, attr)

    def __json__(self):
        return { "type": "download", "href": self.href }


def iri2uri(iri, encoding="utf8"):
    # Character list compiled from RFC 3986, section 2.2
    safe = b":/?#[]@!$&'()*+,;="
    scheme, authority, path, query, frag = urlsplit(iri)

    tpl = authority.split(":", 1)
    if len(tpl) == 1:
        authority = authority.encode('idna')
    else:
        authority = tpl[0].encode('idna') + ":%s" % tpl[1]

    return urlunsplit((scheme.encode(encoding), authority,
                       quote(path.encode(encoding), safe),
                       quote(query.encode(encoding), safe),
                       quote(frag.encode(encoding), safe)))


def urlencode(parameters, doseq=False):
    return _urlencode(parameters, doseq).replace('&', '&amp;')
