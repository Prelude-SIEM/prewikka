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


from prewikka.modules.main import ActionParameters, Actions


def load(core, config):
    # Alerts
    core.setDefaultAction(Actions.AlertListingAction().slot)
    core.interface.registerSection("Alerts", Actions.AlertListingAction().path)
    core.registerAction(Actions.AlertListingAction())
    core.registerAction(Actions.AlertSummaryAction())
    core.registerAction(Actions.AlertDetailsAction())
    core.registerAction(Actions.DeleteAlertsAction())

    # Heartbeats
    core.interface.registerSection("Heartbeats", Actions.HeartbeatListingAction().path)
    core.registerAction(Actions.HeartbeatListingAction())
    core.registerAction(Actions.HeartbeatSummaryAction())
    core.registerAction(Actions.HeartbeatDetailsAction())
    core.registerAction(Actions.DeleteHeartbeatsAction())

    # Sensors
    core.interface.registerSection("Sensors", Actions.SensorListingAction().path)
    core.registerAction(Actions.SensorListingAction())
    core.registerAction(Actions.SensorDeleteAlertsAction())
    core.registerAction(Actions.SensorDeleteHeartbeatsAction())
    core.registerAction(Actions.SensorAlertListingAction())
    core.registerAction(Actions.SensorHeartbeatListingAction())
    core.registerAction(Actions.SensorAlertSummaryAction())
    core.registerAction(Actions.SensorAlertDetailsAction())
    core.registerAction(Actions.SensorHeartbeatSummaryAction())
    core.registerAction(Actions.SensorHeartbeatDetailsAction())
