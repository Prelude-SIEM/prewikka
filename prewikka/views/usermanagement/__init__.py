from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import pluginmanager, version

from . import usermanagement


class UserManagement(pluginmanager.PluginPreload):
    plugin_name = "User management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("User settings page")
    plugin_classes = [usermanagement.UserSettings]
