from alertlisting import AlertListing, SensorAlertListing, CorrelationAlertListing, ToolAlertListing
from heartbeatlisting import HeartbeatListing, SensorHeartbeatListing
from prewikka import pluginmanager, version

class MessageListing(pluginmanager.PluginPreload):
    plugin_name = "Alert and Heartbeat listing"
    plugin_author = "Nicolas Delon, %s" % version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = _("Alert and Heartbeat listing page")

    plugin_classes = [ AlertListing, SensorAlertListing,
                       CorrelationAlertListing, ToolAlertListing,
                       HeartbeatListing, SensorHeartbeatListing ]
