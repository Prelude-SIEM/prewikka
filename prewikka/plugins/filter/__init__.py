from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka import pluginmanager, version

from .filter import FilterView


class FilterPlugin(pluginmanager.PluginPreload):
    plugin_name = "Filters management"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Filters management page")
    plugin_database_branch = version.__branch__
    plugin_database_version = "0"
    plugin_classes = [FilterView]
