from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources

from prewikka import pluginmanager, version


class Statistics(pluginmanager.PluginPreload):
    plugin_name = "Statistics"
    plugin_description = N_("Statistics pages")
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_htdocs = (("statistics", pkg_resources.resource_filename(__name__, 'htdocs')),)
