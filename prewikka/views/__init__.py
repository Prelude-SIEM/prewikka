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


from prewikka.views import \
     messagelisting, messagesummary, messagedetails, sensor, \
     commands, filter, usermanagement, misc



objects = messagelisting.AlertListing(), \
          messagelisting.HeartbeatListing(), \
          messagelisting.SensorAlertListing(), \
          messagelisting.SensorHeartbeatListing(), \
          sensor.SensorListing(), sensor.HeartbeatAnalyze(), sensor.SensorMessagesDelete(), \
          messagesummary.AlertSummary(), messagesummary.HeartbeatSummary(), \
          messagedetails.AlertDetails(), messagedetails.HeartbeatDetails(), \
          commands.Whois(), commands.Traceroute(), \
          filter.AlertFilterEdition(), \
          usermanagement.UserListing(), \
          usermanagement.UserAddForm(), usermanagement.UserAdd(), usermanagement.UserDelete(), \
          usermanagement.UserSettingsDisplay(), usermanagement.UserSettingsModify(), \
          misc.About()



events_section = ("Events", [("Alerts", ["alert_listing"]),
                             ("Heartbeats", ["heartbeat_listing"]),
                             ("Filters", ["filter_edition"])])


agents_section = ("Agents", [("Agents", ["sensor_listing", "sensor_messages_delete", "heartbeat_analyze",
                                         "sensor_alert_listing", "sensor_heartbeat_listing" ])])

users_section = ("Users", [("Users", ["user_listing", "user_add_form", "user_add", "user_delete",
                                      "user_password_change_form", "user_password_change",
                                      "user_permissions_change_form", "user_permissions_change"])])

about_section = ("About", [("About", ["about"])])
