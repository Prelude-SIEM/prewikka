# Copyright (C) 2014-2018 CS-SI. All Rights Reserved.
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

import uuid

from prewikka import error, pluginmanager, resource
from prewikka.utils import cache, html

RED_STD = "E78D90"
ORANGE_STD = "F5B365"
YELLOW_STD = "D4C608"
GREEN_STD = "B1E55D"
BLUE_STD = "93B9DD"
GRAY_STD = "5C5C5C"

SEVERITY_COLOR_MAP = {
    "high": (_("High"), RED_STD),
    "medium": (_("Medium"), ORANGE_STD),
    "low": (_("Low"), GREEN_STD),
    "info": (_("Informational"), BLUE_STD)
}

COLOR_MAP = "93B9DD", "B1E55D", "D4C608", "F5B365", "E78D90", "C6A0CF", "5256D3", \
            "A7DE65", "F2A97B", "F6818A", "B087C6", "66DC92"


class RendererException(Exception):
    pass


class RendererNoDataException(RendererException):
    def __str__(self):
        return _("No data to display.")


class RendererItem(object):
        __slots__ = ["values", "labels", "links", "_tuple"]

        def __init__(self, values=0, labels=None, links=None):
                self._tuple = values, labels, links

                self.values = values
                self.labels = labels
                self.links = links

        def __getitem__(self, i):
                return self._tuple[i]


class RendererUtils(object):
    _nexist_color = (_("n/a"), GRAY_STD)

    def __init__(self, options):
        self._color_map_idx = 0

        self._color_map = options.get("names_and_colors", None)
        if not self._color_map:
            self._color_map = COLOR_MAP

    def get_label(self, label):
        if isinstance(self._color_map, dict):
            return self._color_map.get(label, self._nexist_color)[0]

        return label

    @cache.request_memoize("renderer_color")
    def get_color(self, label, onecolor=False):
        if isinstance(self._color_map, dict):
            return self._color_map.get(label, self._nexist_color)[1]

        color = self._color_map[self._color_map_idx % len(self._color_map)]

        if not onecolor:
            self._color_map_idx += 1

        return color


class RendererBackend(pluginmanager.PluginBase):
    pass


class RendererPluginManager(pluginmanager.PluginManager):
    _default_backends = {}

    def __init__(self):
        self._backends = pluginmanager.PluginManager("prewikka.renderer.backend")
        pluginmanager.PluginManager.__init__(self, "prewikka.renderer.type")

        for typ, backend in env.config.renderer_defaults.items():
            self._default_backends[typ] = backend.value

        self._renderer = {}
        for i in self:
            try:
                self._renderer.setdefault(i.renderer_backend, {})[i.renderer_type] = i()
            except Exception as e:
                env.log.error("%s: %s" % (i.__module__, e))

            if i.renderer_type not in self._default_backends:
                self._default_backends[i.renderer_type] = i.renderer_backend

    def get_types(self):
        return self._default_backends.keys()

    def has_backend(self, wanted_backend, wanted_type=None):
        if wanted_backend not in self._renderer:
            return False

        if wanted_type is None:
            return True

        return set(wanted_type).issubset(self._renderer[wanted_backend])

    def get_backends(self, wanted_type):
        for backend, typedict in self._renderer.items():
            if wanted_type in typedict:
                yield backend

    def get_backends_instances(self, wanted_type):
        for backend in self.get_backends(wanted_type):
            yield self._renderer[backend][wanted_type]

    def get_default_backend(self, wanted_type):
        return self._default_backends.get(wanted_type)

    def render(self, type, data, renderer=None, **kwargs):
        if renderer is None:
            renderer = self.get_default_backend(type)

            if renderer is None:
                raise error.PrewikkaUserError(N_("Renderer error"),
                                              N_("No backend supporting render type '%s'", type))

        if renderer not in self._renderer:
            raise error.PrewikkaUserError(N_("Renderer error"),
                                          N_("No backend named '%s'", renderer))

        if type not in self._renderer[renderer]:
            raise error.PrewikkaUserError(N_("Renderer error"),
                                          N_("Backend '%(backend)s' does not support render type '%(type)s'",
                                             {'backend': renderer, 'type': type}))

        if "names_and_colors" not in kwargs:
            kwargs["names_and_colors"] = COLOR_MAP

        classname = kwargs["class"] = "-".join((renderer, type))
        cssid = kwargs["cssid"] = "-".join((classname, text_type(uuid.uuid4())))

        try:
            data = self._renderer[renderer][type].render(data, **kwargs)
            htmls = resource.HTMLSource('<div id="%s" class="renderer-elem %s">%s</div>'
                                        % (cssid, classname, data.get("html", "")))

            return {"html": htmls, "script": resource.HTMLSource(data.get("script", ""))}
        except RendererNoDataException as e:
            htmls = resource.HTMLSource('<div id="%s" class="renderer-elem renderer-elem-error %s">%s</div>'
                                        % (cssid, classname, text_type(e)))
            script = resource.HTMLSource("""
                 var size = prewikka_getRenderSize("#%s", %s);

                 $("#%s").width(size[0]).css("height", size[1] + 'px').css("line-height", size[1] + 'px');
                """ % (cssid, html.escapejs({k: v for k, v in kwargs.items() if k in ('width', 'height', 'spacing')}), cssid))

            return {"html": htmls, "script": script}
