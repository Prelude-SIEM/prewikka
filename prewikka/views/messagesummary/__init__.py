from __future__ import absolute_import, division, print_function, unicode_literals
from prewikka import pluginmanager, version

from .messagesummary import AlertSummary, HeartbeatSummary


class MessageSummary(pluginmanager.PluginPreload):
    plugin_name = "Detailed alert and heartbeat"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Detailed alert and heartbeat page")
    plugin_classes = [AlertSummary, HeartbeatSummary]
