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
import collections
import string

from prewikka import error, history, hookmanager, resource, response, template, utils, view


CSS_FILES = (
    "prewikka/css/jquery-ui.min.css",
    "prewikka/css/bootstrap.min.css",
    "prewikka/css/jquery-ui-timepicker-addon.min.css",
    "prewikka/css/font-awesome.min.css",
    "prewikka/css/ui.jqgrid.min.css",
    "prewikka/css/ui.multiselect.min.css"
)

JS_FILES = (
    "prewikka/js/json.js",
    "prewikka/js/jquery.js",
    "prewikka/js/jquery-ui.min.js",
    "prewikka/js/bootstrap.min.js",
    "prewikka/js/functions.js",
    "prewikka/js/ajax.js",
    "prewikka/js/underscore-min.js",
    "prewikka/js/jquery-ui-timepicker-addon.min.js",
    "prewikka/js/ui.multiselect.min.js",
    "prewikka/js/jquery.jqgrid.min.js",
    "prewikka/js/commonlisting.js"
)


class BaseView(view._View):
    view_layout = None
    view_template = template.PrewikkaTemplate(__name__, 'templates/baseview.mak')

    @view.route("/download/<int:id>/<filename>")
    @view.route("/download/<int:id>/<filename>/inline", defaults={"inline": True})
    @view.route("/download/<user>/<int:id>/<filename>")
    @view.route("/download/<user>/<int:id>/<filename>/inline", defaults={"inline": True})
    def download(self, user=None, id=None, filename=None, inline=False):
        if user and user != env.request.user.name:
            raise error.PrewikkaUserError(_("Permission Denied"), message=_("Missing permission to access the specified file"), code=403)

        fd = open(utils.mkdownload.get_filename(id, filename, user), "r")
        filename = base64.urlsafe_b64decode(str(filename)).decode("utf8")

        return response.PrewikkaDownloadResponse(fd, filename=filename, inline=inline)

    @staticmethod
    def _get_help_language(lang, default=None):
        for i in ("en", "fr"):
            if i in lang.lower():
                return i

        return default

    @view.route("/help/<path:path>")
    def help(self, path=None):
        server = string.Template(env.config.general.get("help_location"))

        lang = None
        if env.request.user:
            userl = env.request.user.get_property("language")
            if userl:
                lang = self._get_help_language(userl)

        if not lang:
            lang = self._get_help_language(env.config.general.default_locale, "en")

        return response.PrewikkaRedirectResponse(server.substitute(lang=lang, path=path))

    @view.route("/logout")
    def logout(self):
        try:
            env.session.logout(env.request.web)
        except:
            # logout always generate an exception to render the logout template
            pass

        return response.PrewikkaRedirectResponse(env.request.parameters.get("redirect", env.request.web.get_baseurl()), code=302)

    @view.route("/history/<form>/save", methods=["POST"])
    def history_save(self, form):
        if "query" in env.request.parameters:
            history.save(env.request.user, form, env.request.parameters["query"])

        return response.PrewikkaDirectResponse()

    @view.route("/history/<form>/get", methods=["POST"])
    def history_get(self, form):
        queries = history.get(env.request.user, form)
        return response.PrewikkaDirectResponse(queries)

    @view.route("/history/<form>/delete", methods=["POST"])
    def history_delete(self, form):
        query = env.request.parameters["query"] if "query" in env.request.parameters else None
        history.delete(env.request.user, form, query)

        return response.PrewikkaDirectResponse()

    def render(self, *args, **kwargs):
        # FIXME: move theme management to a plugin !
        if env.request.user:
            theme = env.request.user.get_property("theme", default=env.config.general.default_theme)
            lang = env.request.user.get_property("language", default=env.config.general.default_locale)
        else:
            theme = env.config.general.default_theme
            lang = env.config.general.default_locale

        _HEAD = collections.OrderedDict((resource.CSSLink(link), True) for link in CSS_FILES)
        _HEAD[resource.CSSLink("prewikka/css/themes/%s.css" % theme)] = True
        _HEAD.update((resource.JSLink(link), True) for link in JS_FILES)

        # The jqgrid locale files use only two characters for identifying the language (e.g. pt_BR -> pt)
        _HEAD[resource.JSLink("prewikka/js/locales/grid.locale-%s.min.js" % lang[:2])] = True

        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_HEAD_CONTENT")):
            _HEAD.update((i, True) for i in contents)

        _BODY = collections.OrderedDict()
        for contents in filter(None, hookmanager.trigger("HOOK_LOAD_BODY_CONTENT")):
            _BODY.update((i, True) for i in contents)

        env.request.dataset["document"].head_content = _HEAD
        env.request.dataset["document"].body_content = _BODY
        env.request.dataset["toplayout_extra_content"] = filter(None, hookmanager.trigger("HOOK_TOPLAYOUT_EXTRA_CONTENT"))
