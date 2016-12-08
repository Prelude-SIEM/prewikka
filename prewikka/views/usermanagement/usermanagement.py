# Copyright (C) 2004-2016 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>

from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources
from prewikka import error, hookmanager, localization, log, template, theme, usergroup, view


class UserSettingsDisplayParameters(view.Parameters):
    def register(self):
        self.optional("name", str)


class UserSettingsModifyParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("name", str)
        self.optional("email", str)
        self.optional("language", str)
        self.optional("timezone", str)
        self.optional("theme", str)


class UserSettingsDisplay(view.View):
    view_section = N_("Settings")
    view_name = N_("My account")
    view_order = 0

    view_parameters = UserSettingsDisplayParameters
    view_permissions = [ ]
    view_template = template.PrewikkaTemplate(__name__, 'templates/usersettings.mak')
    plugin_htdocs = (("usermanagement", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def render(self):
        login = env.request.parameters.get("name")
        self._object = usergroup.User(login) if login else env.request.user

        if not env.auth.hasUser(self._object):
            raise error.PrewikkaUserError(_("Invalid User"), N_("Requested user '%s' does not exist", self._object))

        env.request.dataset["object"] = self._object
        env.request.dataset["fullname"] = self._object.get_property("fullname")
        env.request.dataset["email"] = self._object.get_property("email")
        env.request.dataset["available_timezones"] = localization.get_timezones()
        env.request.dataset["timezone"] = self._object.get_property("timezone", default=env.config.general.default_timezone)
        env.request.dataset["available_languages"] = localization.getLanguagesAndIdentifiers()
        env.request.dataset["language"] = self._object.get_property("language", default=env.config.general.default_locale)
        env.request.dataset["available_themes"] = theme.getThemes()
        env.request.dataset["selected_theme"] = self._object.get_property("theme", default=env.config.general.default_theme)


class UserSettingsModify(view.View):
    view_name = None
    view_parameters = UserSettingsModifyParameters
    view_permissions = []

    def render(self):
        login = env.request.parameters.get("name", env.request.user.name)
        self._object = user = usergroup.User(login)

        if not env.request.parameters["language"] in localization.getLanguagesIdentifiers():
            raise error.PrewikkaUserError(_("Invalid Language"), N_("Specified language does not exist"), log_priority=log.WARNING)

        list(hookmanager.trigger("HOOK_USERMANAGEMENT_USER_MODIFY", user))
        if not env.request.parameters["timezone"] in localization.get_timezones():
            raise error.PrewikkaUserError(_("Invalid Timezone"), N_("Specified timezone does not exist"), log_priority=log.WARNING)

        user.begin_properties_change()

        for param in ("fullname", "email", "theme", "language", "timezone"):
            user.set_property(param, env.request.parameters.get(param))

        if user == env.request.user:
            user.set_locale()

        user.commit_properties_change()

        # Make sure nothing is returned (reset the default dataset)
        env.request.dataset = None
