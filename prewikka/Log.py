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

EVENT_QUERY = "QUERY"
EVENT_RENDER_VIEW = "PROCESS_RENDER_VIEW"
EVENT_LOGIN_SUCCESSFUL = "LOGIN_SUCCESSFUL"
EVENT_LOGOUT = "LOGOUT"
EVENT_SESSION_EXPIRED = "SESSION_EXPIRED"
EVENT_INVALID_SESSIONID = "INVALID_SESSIONID"
EVENT_BAD_LOGIN = "BAD_LOGIN"
EVENT_BAD_PASSWORD = "BAD_PASSWORD"
EVENT_INVALID_USERID = "INVALID_USERID"
EVENT_INVALID_VIEW = "INVALID_VIEW"
EVENT_INVALID_PARAMETERS = "INVALID_PARAMETERS"
EVENT_VIEW_FORBIDDEN = "VIEW_FORBIDDEN"

EVENT_DEBUG = "DEBUG"
EVENT_INFO = "INFO"
EVENT_ERROR = "ERROR"

TYPE_DEBUG = "DEBUG"
TYPE_INFO = "INFO"
TYPE_ERROR = "ERROR"

_CLASSIFICATIONS = {
    TYPE_DEBUG: [ EVENT_DEBUG, EVENT_QUERY, EVENT_RENDER_VIEW, EVENT_SESSION_EXPIRED ],
    TYPE_INFO: [ EVENT_INFO, EVENT_LOGIN_SUCCESSFUL, EVENT_LOGOUT ],
    TYPE_ERROR: [ EVENT_ERROR, EVENT_INVALID_SESSIONID, EVENT_BAD_LOGIN,
                  EVENT_BAD_PASSWORD, EVENT_INVALID_USERID, EVENT_INVALID_VIEW,
                  EVENT_INVALID_PARAMETERS, EVENT_VIEW_FORBIDDEN ]
    }



def get_event_type(event):
    for type, events in _CLASSIFICATIONS.items():
        if event in events:
            return type



class Log:
    def __init__(self):
        self._backends = [ ]
        
    def registerBackend(self, backend):
        self._backends.append(backend)
        
    def __call__(self, event, request=None, view=None, user=None, details=None):
        for backend in self._backends:
            if event in backend.events:
                apply(backend, (get_event_type(event), event, request, view, user, details))

    def debug(self, request=None, view=None, user=None, details=None):
        self(EVENT_DEBUG, request, view, user, details)

    def info(self, request=None, view=None, user=None, details=None):
        self(EVENT_INFO, request, view, user, details)

    def error(self, request=None, view=None, user=None, details=None):
        self(EVENT_ERROR, request, view, user, details)



class LogBackend:
    def __init__(self, config):
        classifications = copy.copy(_CLASSIFICATIONS)
        for option in config.getOptions():
            if option.name.find("TYPE_") == 0:
                type = option.name
                if option.value == "enable":
                    classifications[type] = _CLASSIFICATIONS[type]
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

        self.events = [ ]
        for events in classifications.values():
            self.events += events



if __name__ == "__main__":
    from MyConfigParser import OrderedDict
    
    config = OrderedDict()
    config[TYPE_ERROR] = "disable"
    config[EVENT_ERROR] = "enable"
    
    backend = LogBackend(config)
    backend.event(EVENT_ERROR, "test")
