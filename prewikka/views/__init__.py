# Copyright (C) 2004,2005 PreludeIDS Technologies. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
#
# This file is part of the Prewikka program.
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


from prewikka.views import \
     messagelisting, alertlisting, heartbeatlisting, messagesummary, messagedetails, sensor, \
     commands, filter, usermanagement, misc

objects = alertlisting.AlertListing(), \
          alertlisting.CorrelationAlertListing(), \
          alertlisting.ToolAlertListing(), \
          alertlisting.SensorAlertListing(), \
          heartbeatlisting.HeartbeatListing(), \
          heartbeatlisting.SensorHeartbeatListing(), \
          sensor.SensorListing(), sensor.HeartbeatAnalyze(), sensor.SensorMessagesDelete(), \
          messagesummary.AlertSummary(), messagesummary.HeartbeatSummary(), \
          messagedetails.AlertDetails(), messagedetails.HeartbeatDetails(), \
          commands.Command(), \
          filter.AlertFilterEdition(), \
          usermanagement.UserListing(), \
          usermanagement.UserAddForm(), usermanagement.UserDelete(), \
          usermanagement.UserSettingsDisplay(), usermanagement.UserSettingsModify(), usermanagement.UserSettingsAdd(), \
          misc.About()



events_section = (_("Events"), [(_("Alerts"), ["alert_listing", "sensor_alert_listing"]),
                             (_("CorrelationAlerts"), ["correlation_alert_listing"]),
                             (_("ToolAlerts"), ["tool_alert_listing"])])


agents_section = (_("Agents"), [(_("Agents"), ["sensor_listing", "sensor_messages_delete", "heartbeat_analyze"]),
                             (_("Heartbeats"), ["heartbeat_listing", "sensor_heartbeat_listing"] )])

settings_section = (_("Settings"), [(_("Users"), ["user_listing", "user_add_form", "user_add", "user_delete",
                                         "user_password_change_form", "user_password_change", "user_settings_display",
                                         "user_settings_modify", "user_permissions_change_form", "user_permissions_change"]),
                                 (_("Filters"), ["filter_edition"])])

about_section = (_("About"), [(_("About"), ["about"])])
