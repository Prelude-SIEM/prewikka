from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import hookmanager, pluginmanager, version

from .usermanagement import (UserSettings, GroupSettings, GenericListing, GroupListingAjax, UserListingAjax)


class UserManagement(pluginmanager.PluginPreload):
    plugin_name = "User and group management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("User and group management pages")
    plugin_classes = [GenericListing, UserListingAjax, GroupListingAjax, UserSettings, GroupSettings]

    @hookmanager.register("HOOK_PROHIBITIVE_FILTER_CRITERIA_IDENTIFIER")
    def _prohibitive_filter_criteria(self, ctype):
        if not env.request.user:
            return

        yield ("user", env.request.user.id)

        for g in env.auth.get_member_of(env.request.user):
            yield ("group", g.id)
