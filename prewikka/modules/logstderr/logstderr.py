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

import prewikka.Log
from prewikka import Interface


class LogStderr(prewikka.Log.LogBackend):
    def _log(self, type, event, message):
        print >> sys.stderr, "[prewikka %s] %s" % (type, message)
        
    def handle_query(self, type, event, request, query):
        self._log(type, event, "query '%s'" % query)

    def handle_action(self, type, event, request, action):
        self._log(type, event, "action %s" % Interface.get_action_name(action))

    def handle_login_successful(self, type, event, request, user):
        self._log(type, event, "user '%s' logged in" % user.getLogin())
        
    def handle_logout(self, type, event, request, user):
        self._log(type, event, "user '%s' logout" % user.getLogin())
        
    def handle_session_expired(self, type, event, request, sessionid):
        self._log(type, event, "session '%s' for user '%s' has expired" % (sessionid, request.user.getLogin()))

    def handle_invalid_sessionid(self, type, event, request, sessionid):
        self._log(type, event, "sessionid '%s' is invalid" % sessionid)

    def handle_bad_login(self, type, event, request, login):
        self._log(type, event, "bad login '%s'" % login)

    def handle_bad_password(self, type, event, request, login, password):
        self._log(type, event, "bad password '%s' for '%s'" % (login, password))

    def handle_invalid_userid(self, type, event, request, userid):
        self._log(type, event, "invalid userid %d" % userid)

    def handle_invalid_action(self, type, event, request, action_name):
        self._log(type, event, "invalid action %s" % action_name)

    def handle_invalid_action_parameters(self, type, event, request, reason):
        self._log(type, event, "invalid action parameters, " + reason)

    def handle_action_denied(self, type, event, request, action):
        self._log(type, event, "action '%s' forbidden for user '%s'" % Interface.get_action_name(action), request.user.getLogin())

    def handle_debug(self, type, event, message):
        self._log(type, event, message)

    def handle_info(self, type, event, message):
        self._log(type, event, message)

    def handle_error(self, type, event, message):
        self._log(type, event, message)



def load(core, config):
    backend = LogStderr(config)
    core.log.registerBackend(backend)
