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


class Log:
    def __init__(self):
        self._backends = [ ]

    def registerBackend(self, backend):
        self._backends.append(backend)

    def _applyOnBackends(self, handler, *args, **kwargs):
        for backend in self._backends:
            apply(getattr(backend, handler), args, kwargs)

    def invalidQuery(self, request, error):
        self._applyOnBackends("invalidQuery", request, error)



class LogBackend:
    def invalidQuery(self, request, error):
        pass
