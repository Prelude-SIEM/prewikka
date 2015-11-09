from . import usermanagement
from prewikka import pluginmanager, version

class UserManagement(pluginmanager.PluginPreload):
    plugin_name = "User management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("User settings page")
    plugin_classes = [ usermanagement.UserSettingsDisplay, usermanagement.UserSettingsModify ]
