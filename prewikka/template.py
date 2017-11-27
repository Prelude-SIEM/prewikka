# Copyright (C) 2014-2017 CS-SI. All Rights Reserved.
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

import collections
import os.path
import mako.exceptions
import mako.lookup
import mako.template
import pkg_resources

from prewikka import siteconfig
from prewikka.utils import cache


_MAKO_FILTERS = ["html.escape"]
_MAKO_GENERIC_ARGS = {
    "default_filters": _MAKO_FILTERS,
    "buffer_filters": _MAKO_FILTERS,
    "input_encoding": 'utf8', "imports": [
        'from prewikka.utils import html, json',
        'from prewikka.utils.html import checked, disabled, selected'
    ],
    "future_imports": ["unicode_literals"],
    "module_directory": os.path.join(siteconfig.tmp_dir, "mako")
}

_MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_MAKO_TEMPLATE_LOOKUP = mako.lookup.TemplateLookup(directories=[_MODULE_PATH], **_MAKO_GENERIC_ARGS)


# We cannot inherit dict directly because it's __json__() method would never be called. Simplejson
# only call the user provided encoding callback when the object is not known to be serializable.

class _Dataset(collections.MutableMapping):
    def __init__(self, template, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._template = template

    def render(self):
        return self._template.render(**self._d)

    def __json__(self):
        return self.render()

    def __len__(self):
        return self._d.__len__()

    def __setitem__(self, key, value):
        return self._d.__setitem__(key, value)

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def __delitem__(self, key):
        return self._d.__delitem__(key)

    def __iter__(self):
        return self._d.__iter__()


class _PrewikkaTemplate(object):
    def dataset(self, *args, **kwargs):
        return _Dataset(self, *args, **kwargs)

    def __init__(self, *args):
        if len(args) == 2:
            self._name = pkg_resources.resource_filename(*args)
        else:
            self._name = args[0]

        self._error = None

        try:
            self._template = mako.template.Template(filename=self._name, lookup=_MAKO_TEMPLATE_LOOKUP, **_MAKO_GENERIC_ARGS)
        except Exception as e:
            self._error = e

    def __json__(self):
        return self._template.render()

    def render(self, **kwargs):
        if self._error:
            raise self._error

        return self._template.render(**kwargs)


class _PrewikkaTemplateProxy(object):
    @cache.memoize("cache")
    def __call__(self, *args):
        return _PrewikkaTemplate(*args)

    @classmethod
    def __instancecheck__(cls, instance):
        return isinstance(instance, (_PrewikkaTemplate, _Dataset))


PrewikkaTemplate = _PrewikkaTemplateProxy()
