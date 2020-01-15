# Copyright (C) 2018-2020 CS-SI. All Rights Reserved.
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

import re

from prewikka import resource, utils


_SENTINEL = object()


class LinkManager(object):
    """Contextual link manager"""

    def __init__(self):
        self._links = {}

        for i in env.config.url:
            self._init_url(i.get_instance_name() or "other", i)

    def add_link(self, label, paths, urlgencb):
        self._register_link(paths, label, urlgencb)

    def _register_link(self, paths, label, url):
        for path in paths:
            self._links.setdefault(path, []).append((label, url))

    def _init_url(self, type, config):
        for option, value in config.items():
            if not self._check_option(option, value):
                continue

            paths = filter(None, re.split('\s|,', config.get("paths", "")))
            self._register_link(list(paths) + [type], option, value)

    def _check_option(self, option, value):
        return option != "paths"

    def get_links(self, path=None, arg=None):
        if arg is None:
            raise ValueError("Parameter 'arg' cannot be None")

        d = {path: self._links.get(path, [])} if path else self._links

        for path, links in d.items():
            for label, url in links:
                yield self._get_link(label, url, arg, path=path)

    def _get_link(self, label, value, arg, path=None):
        d = {"data-path": path} if path else {}
        if callable(value):
            value = value(arg)
        else:
            value = value.replace("$value", utils.url.quote_plus(arg.encode("utf-8")))

        return resource.HTMLNode("a", _(label.capitalize()), href=value, **d)
