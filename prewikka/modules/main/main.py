# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.


from prewikka import Interface
from prewikka.modules.main import ActionParameters, Actions

def load(core, config):
    # Alerts
    core.interface.registerSection("Alerts", Actions.AlertListing())
    core.interface.registerAction(Actions.AlertListing(), ActionParameters.MessageListing, default=True)
    core.interface.registerAction(Actions.AlertSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.AlertDetails(), ActionParameters.Message)
    core.interface.registerAction(Actions.DeleteAlerts(), ActionParameters.MessageListingDelete)
    
    # Heartbeats
    core.interface.registerSection("Heartbeats", Actions.HeartbeatsAnalyze())
    core.interface.registerAction(Actions.HeartbeatListing(), ActionParameters.MessageListing)
    core.interface.registerAction(Actions.HeartbeatsAnalyze(), Interface.ActionParameters)
    core.interface.registerAction(Actions.HeartbeatSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.HeartbeatDetails(), ActionParameters.Message)
    core.interface.registerAction(Actions.DeleteHeartbeats(), ActionParameters.MessageListingDelete)

    # Sensors
    core.interface.registerSection("Sensors", Actions.SensorListing())
    core.interface.registerAction(Actions.SensorListing(), Interface.ActionParameters)
    core.interface.registerAction(Actions.SensorDeleteAlerts(), ActionParameters.SensorMessageListingDelete)
    core.interface.registerAction(Actions.SensorDeleteHeartbeats(), ActionParameters.SensorMessageListingDelete)
    core.interface.registerAction(Actions.SensorAlertListing(), ActionParameters.SensorMessageListing)
    core.interface.registerAction(Actions.SensorHeartbeatListing(), ActionParameters.SensorMessageListing)
    core.interface.registerAction(Actions.SensorAlertSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.SensorAlertDetails(), ActionParameters.Message)
    core.interface.registerAction(Actions.SensorHeartbeatSummary(), ActionParameters.Message)
    core.interface.registerAction(Actions.SensorHeartbeatDetails(), ActionParameters.Message)
