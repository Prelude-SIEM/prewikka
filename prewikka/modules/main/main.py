from prewikka.modules.main import ActionParameters, Actions, View

def load(core, config):
    # Alerts
    core.interface.registerSection("Alerts", Actions.AlertListing())
    core.interface.registerAction(Actions.AlertListing(), ActionParameters.Listing, default=True)
    core.interface.registerAction(Actions.AlertSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.AlertDetails(), ActionParameters.Message)
    core.interface.registerAction(Actions.DeleteAlerts(), ActionParameters.Delete)

    # Heartbeats
    core.interface.registerSection("Heartbeats", Actions.HeartbeatListing())
    core.interface.registerAction(Actions.HeartbeatListing(), ActionParameters.Listing)
    core.interface.registerAction(Actions.HeartbeatSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.HeartbeatDetails(), ActionParameters.Message)
    core.interface.registerAction(Actions.DeleteHeartbeats(), ActionParameters.Delete)
