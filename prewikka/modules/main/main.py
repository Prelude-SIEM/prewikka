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
    core.setDefaultAction(Actions.AlertListing().slot)
    core.interface.registerSection("Alerts", Actions.AlertListing().path)
    core.registerAction(Actions.AlertListing())
    core.registerAction(Actions.AlertSummary())
    core.registerAction(Actions.AlertDetails())
    core.registerAction(Actions.DeleteAlerts())

    # Heartbeats
    core.interface.registerSection("Heartbeats", Actions.HeartbeatListing().path)
    core.registerAction(Actions.HeartbeatListing())
    core.registerAction(Actions.HeartbeatSummary())
    core.registerAction(Actions.HeartbeatDetails())
    core.registerAction(Actions.DeleteHeartbeats())

    # Sensors
    core.interface.registerSection("Sensors", Actions.SensorListing().path)
    core.registerAction(Actions.SensorListing())
    core.registerAction(Actions.SensorDeleteAlerts())
    core.registerAction(Actions.SensorDeleteHeartbeats())
    core.registerAction(Actions.SensorAlertListing())
    core.registerAction(Actions.SensorHeartbeatListing())
    core.registerAction(Actions.SensorAlertSummary())
    core.registerAction(Actions.SensorAlertDetails())
    core.registerAction(Actions.SensorHeartbeatSummary())
    core.registerAction(Actions.SensorHeartbeatDetails())
