# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
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

import copy
import itertools

import pkg_resources
from prewikka import hookmanager, resource, template, utils, view

_CSS_FILES = utils.OrderedDict((resource.CSSLink(link), True) for link in (
    "prewikka/css/jquery-ui.min.css",
    "prewikka/css/bootstrap.min.css",
    "prewikka/css/jquery.jstree.css",
    "prewikka/css/jquery-ui-timepicker-addon.min.css",
    "prewikka/css/font-awesome.min.css",
    "prewikka/css/ui.jqgrid.min.css",
    "prewikka/css/ui.multiselect.min.css",
    "prewikka/css/loader.css")
)


_JS_FILES = utils.OrderedDict((resource.JSLink(link), True) for link in (
    "prewikka/js/jquery.js",
    "prewikka/js/jquery-ui.min.js",
    "prewikka/js/bootstrap.min.js",
    "prewikka/js/functions.js",
    "prewikka/js/ajax.js",
    "prewikka/js/underscore-min.js",
    "prewikka/js/jquery-ui-timepicker-addon.min.js",
    "prewikka/js/ui.multiselect.min.js",
    "prewikka/js/jquery.jqgrid.min.js",
    "prewikka/js/commonlisting.js",
    "prewikka/js/jquery.jstree.js")
)


class BaseView(view._View):
    view_template = template.PrewikkaTemplate(__name__, 'templates/baseview.mak')

    def render(self):
        # FIXME: move theme management to a plugin !
        if env.request.user:
            theme = env.request.user.get_property("theme", default=env.config.general.default_theme)
            lang = env.request.user.get_property("language", default=env.config.general.default_locale)
        else:
            theme = env.config.general.default_theme
            lang = env.config.general.default_locale

        _HEAD = copy.copy(_CSS_FILES)
        _HEAD[resource.CSSLink("prewikka/css/themes/%s.css" % theme)] = True
        _HEAD.update(_JS_FILES)

        # The jqgrid locale files use only two characters for identifying the language (e.g. pt_BR -> pt)
        _HEAD[resource.JSLink("prewikka/js/locales/grid.locale-%s.js" % lang[:2])] = True

        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_HEAD_CONTENT")):
            _HEAD.update((i, True) for i in contents)

        _BODY = utils.OrderedDict()
        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_BODY_CONTENT")):
            _BODY.update((i, True) for i in contents)

        self.dataset["document"].head_content = _HEAD
        self.dataset["document"].body_content = _BODY
        self.dataset["toplayout_extra_content"] = filter(None, hookmanager.trigger("HOOK_TOPLAYOUT_EXTRA_CONTENT"))
