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


from prewikka import Interface, Action
from prewikka.UserManagement import CAPABILITY_READ_MESSAGE, CAPABILITY_DELETE_MESSAGE, \
     CAPABILITY_USER_MANAGEMENT
from prewikka.modules.main import ActionParameters, Actions


def load(core, config):
    # Alerts
    core.interface.registerSection("Alerts", Actions.AlertListing())
    core.registerAction(Actions.AlertListing(), ActionParameters.MessageListing, [ CAPABILITY_READ_MESSAGE ], default=True)
    core.registerAction(Actions.AlertSummary(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.AlertDetails(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.DeleteAlerts(), ActionParameters.MessageListingDelete, [ CAPABILITY_DELETE_MESSAGE ])
    
    # Heartbeats
    core.interface.registerSection("Heartbeats", Actions.HeartbeatListing())
    core.registerAction(Actions.HeartbeatListing(), ActionParameters.MessageListing, [ CAPABILITY_READ_MESSAGE ])
    #i.registerAction(Actions.HeartbeatsAnalyze(), Interface.ActionParameters, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.HeartbeatSummary(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.HeartbeatDetails(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.DeleteHeartbeats(), ActionParameters.MessageListingDelete, [ CAPABILITY_DELETE_MESSAGE ])

    # Sensors
    core.interface.registerSection("Sensors", Actions.SensorListing())
    core.registerAction(Actions.SensorListing(), Action.ActionParameters, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorDeleteAlerts(), ActionParameters.SensorMessageListingDelete, [ CAPABILITY_DELETE_MESSAGE ])
    core.registerAction(Actions.SensorDeleteHeartbeats(), ActionParameters.SensorMessageListingDelete, [ CAPABILITY_DELETE_MESSAGE ])
    core.registerAction(Actions.SensorAlertListing(), ActionParameters.SensorMessageListing, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorHeartbeatListing(), ActionParameters.SensorMessageListing, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorAlertSummary(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorAlertDetails(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorHeartbeatSummary(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
    core.registerAction(Actions.SensorHeartbeatDetails(), ActionParameters.Message, [ CAPABILITY_READ_MESSAGE ])
