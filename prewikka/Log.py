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

    def __del__(self):
        return "destroy Log"
        
    def registerBackend(self, backend):
        self._backends.append(backend)
        
    def __call__(self, event, *args, **kwargs):
        for backend in self._backends:
            apply(backend.event, (event, ) + args, kwargs)

    def debug(self, message):
        self(EVENT_DEBUG, message)

    def info(self, message):
        self(EVENT_INFO, message)

    def error(self, message):
        self(EVENT_ERROR, message)



class LogBackend:
    def __init__(self, config):
        classifications = copy.copy(CLASSIFICATIONS)
        for option in config.getOptions():
            if option.name.find("TYPE_") == 0:
                type = option.name
                if option.value == "enable":
                    classifications[type] = CLASSIFICATIONS[type]
                else:
                    del classifications[type]
            elif option.name.find("EVENT_") == 0:
                event = option.name
                type = get_event_type(event)
                if option.value == "enable":
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
        self.current_event = event
        self.current_event_type = get_event_type(event)
        apply(getattr(self, handler), args, kwargs)
        
    def handle_query(self, request, query):
        pass

    def handle_action(self, request, action_name):
        pass

    def handle_login_successful(self, request, user, sessionid):
        pass

    def handle_logout(self, request, user):
        pass

    def handle_session_expired(self, request, sessionid):
        pass

    def handle_invalid_sessionid(self, request, sessionid):
        pass

    def handle_bad_login(self, request, login):
        pass

    def handle_bad_password(self, request, user, password):
        pass

    def handle_invalid_userid(self, request, userid):
        pass

    def handle_invalid_action(self, request, action_name):
        pass

    def handle_invalid_action_parameters(self, request, reason):
        pass

    def handle_action_denied(self, request, action_name):
        pass

    def handle_debug(self, message):
        pass

    def handle_info(self, message):
        pass

    def handle_error(self, message):
        pass


            
if __name__ == "__main__":
    from MyConfigParser import OrderedDict
    
    config = OrderedDict()
    config[TYPE_ERROR] = "disable"
    config[EVENT_ERROR] = "enable"
    
    backend = LogBackend(config)
    backend.event(EVENT_ERROR, "test")
