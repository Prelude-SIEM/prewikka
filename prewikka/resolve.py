# Copyright (C) 2008 PreludeIDS Technologies. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
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

import time
import socket

resolver = None
import_fail = None

try:
    from twisted.internet import reactor
    from twisted.names import client, dns, hosts, cache, resolve
except Exception, err:
    import_fail = err

try:
    from threading import Lock
except ImportError:
    from dummy_threading import Lock

class DNSResolver:
    def __init__(self):
        self._query = 0
        self._lock = Lock()

        self._cache = cache.CacheResolver()
        rlist = [ self._cache, client.Resolver('/etc/resolv.conf') ]
        self._resolve = resolve.ResolverChain(rlist)

    def _error_cb(self, failure):
        self._query -= 1

        if failure.check(dns.DomainError, dns.AuthoritativeDomainError):
            return

    def _resolve_cb(self, (ans, auth, add), ptr, resolve_cb):
        self._query -= 1

        resolve_cb(str(ans[0].payload.name))

        q = dns.Query(str(ans[0].name), ans[0].type, ans[0].cls)
        self._cache.cacheResult(q, (ans, auth, add))

    def _ip_reverse(self, addr):
        try:
            parts = list(socket.inet_pton(socket.AF_INET6, addr).encode('hex_codec'))
            origin = ".ip6.arpa"
        except:
            parts = ["%d" % ord(byte) for byte in socket.inet_aton(addr)]
            origin = ".in-addr.arpa"

        parts.reverse()
        return '.'.join(parts) + origin

    def process(self, timeout=0):
        end = now = time.time()
        final = now + timeout

        while True:
            self._lock.acquire()

            if self._query == 0:
                self._lock.release()
                break

            reactor.runUntilCurrent();
            reactor.doIteration(timeout)

            self._lock.release()

            end = time.time()
            if end >= final:
                break

        #print "max=%f elapsed:%f" % (timeout, end-now)

    def doQuery(self, addr, resolve_cb):
        self._lock.acquire()

        self._query += 1
        self._resolve.lookupPointer(addr).addCallback(self._resolve_cb, addr, resolve_cb).addErrback(self._error_cb)

        self._lock.release()
        self.process()

    def resolve(self, addr, resolve_cb):
        try:
            addr = self._ip_reverse(addr)
        except:
            return

        self.doQuery(addr, resolve_cb)
        self.process()


class AddressResolve:
    def _resolve_cb(self, value):
        self._name = value

    def __init__(self, addr):
        global resolver

        self._addr = addr
        self._name = None

        if resolver:
            resolver.resolve(addr, self._resolve_cb)

    def __len__(self):
        return len(str(self))

    def __str__(self):
        if resolver:
            resolver.process()

        return self._name or self._addr

    def __repr__(self):
        return str(self)


def init(env):
    global resolver

    if env.dns_max_delay == -1:
        return

    if import_fail:
       env.log.warning("Asynchronous DNS resolution disabled: twisted.names and twisted.internet required: %s" % err)
       return

    resolver = DNSResolver()

