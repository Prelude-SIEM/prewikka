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


from prewikka import view, resource, hookmanager, env, templates


_CSS_FILES = [resource.CSSLink(link) for link in (
    "prewikka/css/jquery-ui.min.css",
    "prewikka/css/bootstrap.min.css",
    "prewikka/css/jquery.jstree.css",
    "prewikka/css/jquery-ui-timepicker-addon.min.css",
    "prewikka/css/font-awesome.min.css",
    "prewikka/css/ui.jqgrid.min.css",
    "prewikka/css/ui.multiselect.css",
    "prewikka/css/loader.css")
]

_JS_FILES = [resource.JSLink(link) for link in (
    "prewikka/js/jquery.js",
    "prewikka/js/jquery-ui.min.js",
    "prewikka/js/bootstrap.min.js",
    "prewikka/js/functions.js",
    "prewikka/js/ajax.js",
    "prewikka/js/underscore-min.js",
    "prewikka/js/jquery-ui-timepicker-addon.min.js",
    "prewikka/js/ui.multiselect.js",
    "prewikka/js/jquery.jqgrid.min.js",
    "prewikka/js/commonlisting.js",
    "prewikka/js/jquery.jstree.js")
]


class BaseView(view._View):
    view_template = templates.BaseView

    def render(self):
        # The database attribute might be None in case of initialisation error
        # FIXME: move me to a plugin !
        try:
            theme_name = env.request.user.get_property("theme", default=env.config.general.default_theme)
        except:
            theme_name = env.config.general.default_theme

        theme_file = resource.CSSLink("prewikka/css/themes/%s.css" % theme_name)
        head = _CSS_FILES + [theme_file] + _JS_FILES

        for i in hookmanager.trigger("HOOK_LOAD_HEAD_CONTENT"):
            head += (content for content in i if content not in head)

        self.dataset["document.head_content"] = head
        self.dataset["toplayout_extra_content"] = ""

        list(hookmanager.trigger("HOOK_TOPLAYOUT_EXTRA_CONTENT", self.dataset))
