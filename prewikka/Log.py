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


import copy

EVENT_QUERY = "EVENT_QUERY"
EVENT_ACTION = "EVENT_ACTION"
EVENT_LOGIN_SUCCESSFUL = "EVENT_LOGIN_SUCCESSFUL"
EVENT_LOGOUT = "EVENT_LOGOUT"
EVENT_SESSION_EXPIRED = "EVENT_SESSION_EXPIRED"
EVENT_INVALID_SESSIONID = "EVENT_INVALID_SESSIONID"
EVENT_BAD_LOGIN = "EVENT_BAD_LOGIN"
EVENT_BAD_PASSWORD = "EVENT_BAD_PASSWORD"
EVENT_INVALID_USERID = "EVENT_INVALID_USERID"
EVENT_INVALID_ACTION = "EVENT_INVALID_ACTION"
EVENT_INVALID_ACTION_PARAMETERS = "EVENT_INVALID_ACTION_PARAMETERS"
EVENT_ACTION_DENIED = "EVENT_ACTION_DENIED"

EVENT_DEBUG = "EVENT_DEBUG"
EVENT_INFO = "EVENT_INFO"
EVENT_ERROR = "EVENT_ERROR"

TYPE_DEBUG = "TYPE_DEBUG"
TYPE_INFO = "TYPE_INFO"
TYPE_ERROR = "TYPE_ERROR"

CLASSIFICATIONS = {
    TYPE_DEBUG: [ EVENT_DEBUG, EVENT_QUERY, EVENT_ACTION, EVENT_SESSION_EXPIRED ],
    TYPE_INFO: [ EVENT_INFO, EVENT_LOGIN_SUCCESSFUL, EVENT_LOGOUT ],
    TYPE_ERROR: [ EVENT_ERROR, EVENT_INVALID_SESSIONID, EVENT_BAD_LOGIN,
                  EVENT_BAD_PASSWORD, EVENT_INVALID_USERID, EVENT_INVALID_ACTION,
                  EVENT_INVALID_ACTION_PARAMETERS, EVENT_ACTION_DENIED ]
    }



def get_event_type(event):
    for type, events in CLASSIFICATIONS.items():
        if event in events:
            return type



class Log:
    def __init__(self):
        self._backends = [ ]
        
    def registerBackend(self, backend):
        self._backends.append(backend)
        
    def event(self, event, *args, **kwargs):
        for backend in self._backends:
            apply(backend.event, (event, ) + args, kwargs)

    def debug(self, message):
        self.event(EVENT_DEBUG, message)

    def info(self, message):
        self.event(EVENT_INFO, message)

    def error(self, message):
        self.event(EVENT_ERROR, message)



class LogBackend:
    def __init__(self, config):
        classifications = copy.copy(CLASSIFICATIONS)
        for key, value in config.items():
            if key.find("TYPE_") == 0:
                type = key
                if value == "enable":
                    classifications[type] = CLASSIFICATIONS[type]
                else:
                    del classifications[type]
            elif key.find("EVENT_") == 0:
                event = key
                type = get_event_type(event)
                if value == "enable":
                    try:
                        if not event in classifications[type]:
                            classifications[type].append(event)
                    except KeyError:
                        classifications[type] = [ event ]
                else:
                    classifications[type].remove(event)

        self._events = [ ]
        for events in classifications.values():
            self._events += events
        
    def event(self, event, *args, **kwargs):
        if not event in self._events:
            return
        
        handler = event.lower().replace("event", "handle", 1)
        apply(getattr(self, handler), (get_event_type(event), event) + args, kwargs)
        
    def handle_query(self, type, event, request, query):
        pass

    def handle_action(self, type, event, request, action):
        pass

    def handle_login_successful(self, type, event, request, user):
        pass

    def handle_logout(self, type, event, request, user):
        pass

    def handle_session_expired(self, type, event, request, sessionid):
        pass

    def handle_invalid_sessionid(self, type, event, request, sessionid):
        pass

    def handle_bad_login(self, type, event, request, login):
        pass

    def handle_bad_password(self, type, event, request, user, password):
        pass

    def handle_invalid_userid(self, type, event, request, userid):
        pass

    def handle_invalid_action(self, type, event, request, action_name):
        pass

    def handle_invalid_action_parameters(self, type, event, request, reason):
        pass

    def handle_action_denied(self, type, event, request, action):
        pass

    def handle_debug(self, type, event, message):
        pass

    def handle_info(self, type, event, message):
        pass

    def handle_error(self, type, event, message):
        pass


            
if __name__ == "__main__":
    from MyConfigParser import OrderedDict
    
    config = OrderedDict()
    config[TYPE_ERROR] = "disable"
    config[EVENT_ERROR] = "enable"
    
    backend = LogBackend(config)
    backend.event(EVENT_ERROR, "test")
