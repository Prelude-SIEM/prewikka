# Copyright (C) 2004-2019 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>

from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources
from enum import IntEnum

from prewikka import error, hookmanager, localization, log, response, template, theme, usergroup, view


ReloadEnum = IntEnum("ReloadEnum", "none view window")


class UserSettings(view.View):
    plugin_htdocs = (("usermanagement", pkg_resources.resource_filename(__name__, 'htdocs')),)

    @view.route("/settings/my_account", menu=(N_("Preferences"), N_("My account")), help="#myaccount")
    def display(self):
        self._object = env.request.user

        if not env.auth.has_user(self._object):
            raise error.PrewikkaUserError(N_("Invalid User"), N_("Requested user '%s' does not exist", self._object))

        dataset = {}
        dataset["object"] = self._object
        dataset["fullname"] = self._object.get_property("fullname")
        dataset["email"] = self._object.get_property("email")
        dataset["available_timezones"] = localization.get_timezones()
        dataset["timezone"] = self._object.get_property("timezone", default=env.config.general.default_timezone)
        dataset["available_languages"] = localization.get_languages()
        dataset["language"] = self._object.get_property("language", default=env.config.general.default_locale)
        dataset["available_themes"] = theme.get_themes()
        dataset["selected_theme"] = self._object.get_property("theme", default=env.config.general.default_theme)

        return template.PrewikkaTemplate(__name__, 'templates/usersettings.mak').render(**dataset)

    @view.route("/settings/my_account", methods=["POST"])
    def modify(self):
        self._object = user = usergroup.User(env.request.parameters.get("name", env.request.user.name))

        if not env.request.parameters["language"] in localization.get_languages():
            raise error.PrewikkaUserError(N_("Invalid Language"), N_("Specified language does not exist"), log_priority=log.WARNING)

        list(hookmanager.trigger("HOOK_USERMANAGEMENT_USER_MODIFY", user))
        if not env.request.parameters["timezone"] in localization.get_timezones():
            raise error.PrewikkaUserError(N_("Invalid Timezone"), N_("Specified timezone does not exist"), log_priority=log.WARNING)

        reload_type = ReloadEnum["none"]
        for param, reload in (("fullname", "none"), ("email", "none"), ("timezone", "view"), ("theme", "window"), ("language", "window")):
            value = env.request.parameters.get(param)
            if value != user.get_property(param):
                if value:
                    user.set_property(param, value)
                else:
                    user.del_property(param)

                reload_type = max(reload_type, ReloadEnum[reload])

        if user == env.request.user:
            user.set_locale()

        user.sync_properties()

        # Make sure nothing is returned (reset the default dataset)
        env.request.dataset = None

        if reload_type > ReloadEnum["none"]:
            return response.PrewikkaResponse({"type": "reload", "target": reload_type.name})

        return response.PrewikkaRedirectResponse(url_for(".display"), 303)
