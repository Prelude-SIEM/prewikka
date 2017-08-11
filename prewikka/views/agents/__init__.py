from __future__ import absolute_import, division, print_function, unicode_literals
from prewikka import pluginmanager, version
from .agents import Agents


class AgentPlugin(pluginmanager.PluginPreload):
    plugin_name = "Agents status"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Agents status information page")
    plugin_classes = [Agents]
