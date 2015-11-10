# Copyright (C) 2004-2015 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>

import pkg_resources

from prewikka import view, localization, theme, log, usergroup, error, env
from . import templates


class UserSettingsDisplayParameters(view.Parameters):
    def register(self):
        self.optional("name", str)


class UserSettingsModifyParameters(view.Parameters):
    allow_extra_parameters = True

    def register(self):
        self.optional("name", str)
        self.optional("email", str)
        self.optional("language", str)
        self.optional("theme", str)


class UserSettingsDisplay(view.View):
    view_section = N_("Settings")
    view_name = N_("My account")
    view_order = 0

    view_parameters = UserSettingsDisplayParameters
    view_permissions = [ ]
    view_template = templates.UserSettings
    plugin_htdocs = (("usermanagement", pkg_resources.resource_filename(__name__, 'htdocs')),)

    def render(self):
        login = self.parameters.get("name")
        self._object = usergroup.User(login) if login else self.user

        if not env.auth.hasUser(self._object):
            raise error.PrewikkaUserError(_("Invalid User"), _("Requested user '%s' does not exist") % self._object)

        self.dataset["object"] = self._object
        self.dataset["fullname"] = env.db.get_property(self._object, "fullname")
        self.dataset["email"] = env.db.get_property(self._object, "email")
        self.dataset["available_languages"] = localization.getLanguagesAndIdentifiers()
        self.dataset["language"] = env.db.get_property(self._object, "language", default=env.config.default_locale)
        self.dataset["available_themes"] = theme.getThemes()
        self.dataset["user.theme"] = env.db.get_property(self._object, "theme", default=env.config.default_theme)


class UserSettingsModify(view.View):
    view_name = None
    view_parameters = UserSettingsModifyParameters
    view_permissions = []

    def render(self):
        login = self.parameters.get("name", self.user.name)

        self._object = user = usergroup.User(login)

        env.db.set_property(user, "fullname", self.parameters.get("fullname"))
        env.db.set_property(user, "email", self.parameters.get("email"))
        env.db.set_property(user, "theme", self.parameters.get("theme"))

        lang = self.parameters["language"]
        if not lang in localization.getLanguagesIdentifiers():
            raise error.PrewikkaUserError(_("Invalid Language"), _("Specified language does not exist"), log_priority=log.WARNING)

        env.db.set_property(user, "language", lang)
        if user == self.user:
            self.user.set_locale()

        # Make sure nothing is returned (reset the default dataset)
        self.dataset = None
