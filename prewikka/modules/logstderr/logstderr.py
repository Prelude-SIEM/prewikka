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


import sys
import os

from prewikka import Log, Interface


class LogStderr(Log.LogBackend):
    def _log(self, message):
        type = { Log.TYPE_DEBUG: "debug",
                 Log.TYPE_INFO: "info",
                 Log.TYPE_ERROR: "error" }[self.current_event_type]
        print >> sys.stderr, "[prewikka:%s] %s" % (type, message)
        
    def handle_query(self, request, query):
        self._log("query '%s'" % query)

    def handle_action(self, request, action_name):
        self._log("action %s" % action_name)
        
    def handle_login_successful(self, request, user, sessionid):
        self._log("user '%s' logged in, sessionid %s set" % (user.login, sessionid))
        
    def handle_logout(self, request, user):
        self._log("user '%s' logout" % user.login)
        
    def handle_session_expired(self, request, login, sessionid):
        self._log("session '%s' for user '%s' has expired" % (sessionid, login))

    def handle_invalid_sessionid(self, request, sessionid):
        self._log("sessionid '%s' is invalid" % sessionid)

    def handle_bad_login(self, request, login):
        self._log("bad login '%s'" % login)

    def handle_bad_password(self, request, login, password):
        self._log("bad password '%s' for '%s'" % (password, login))

    def handle_invalid_userid(self, request, userid):
        self._log("invalid userid %d" % userid)

    def handle_invalid_action(self, request, action_name):
        self._log("invalid action %s" % action_name)

    def handle_invalid_action_parameters(self, request, reason):
        self._log("invalid action parameters, " + reason)

    def handle_action_denied(self, request, action_name):
        self._log("action '%s' forbidden for user '%s'" % (action_name, request.user.login))

    def handle_debug(self, message):
        self._log(message)

    def handle_info(self, message):
        self._log(message)

    def handle_error(self, message):
        self._log(message)



def load(core, config):
    backend = LogStderr(config)
    core.log.registerBackend(backend)
