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
     messagelisting, messagesummary, messagedetails, sensor, admin, \
     commands, filter, usermanagement



objects = messagelisting.AlertListing(), \
          messagelisting.HeartbeatListing(), \
          messagelisting.SensorAlertListing(), \
          messagelisting.SensorHeartbeatListing(), \
          messagelisting.AlertDelete(), messagelisting.HeartbeatDelete(), \
          messagelisting.SensorAlertDelete(), messagelisting.SensorHeartbeatDelete(), \
          sensor.SensorListing(), sensor.HeartbeatAnalyze(), admin.Admin(), \
          messagesummary.AlertSummary(), messagesummary.HeartbeatSummary(), \
          messagedetails.AlertDetails(), messagedetails.HeartbeatDetails(), \
          commands.Whois(), commands.Traceroute(), \
          filter.AlertFilterEdition(), \
          usermanagement.UserListing(), \
          usermanagement.UserAddForm(), usermanagement.UserAdd(), \
          usermanagement.UserDelete(), \
          usermanagement.PasswordChangeForm(), usermanagement.PasswordChange(), \
          usermanagement.PermissionsChangeForm(), usermanagement.PermissionsChange()



sections = [("Events", (("Alerts", ["alert_listing", "alert_delete"]),
                        ("Heartbeats", ["heartbeat_listing", "heartbeat_delete"]),
                        ("Filters", ["alert_filter_edition", "alert_filter_load"]))),
            ("Agents", (("Agents", ["sensor_listing", "heartbeat_analyze",
                                    "sensor_alert_listing", "sensor_heartbeat_listing",
                                    "sensor_alert_delete", "sensor_heartbeat_delete",
                                    "admin_config_display", "admin_option_change",
                                    "admin_instance_create", "admin_destroy"]),)),
            ("Users", (("Users", ["user_listing", "user_add_form", "user_add", "user_delete",
                                  "user_password_change_form", "user_password_change",
                                  "user_permissions_change_form", "user_permissions_change"]), ))]
