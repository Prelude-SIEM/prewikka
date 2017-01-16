# Copyright (C) 2008-2017 CS-SI. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from __future__ import absolute_import, division, print_function, unicode_literals

import socket
import time

from prewikka import compat

resolver = None
import_fail = None

try:
    from twisted.internet import reactor
    from twisted.names import client, dns, hosts, cache, resolve
except Exception as err:
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

    def _resolve_cb(self, tpl, ptr, resolve_cb):
        ans, auth, add = tpl

        self._query -= 1
        name = str(ans[0].payload.name)

        resolve_cb(name)

        q = dns.Query(name, ans[0].type, ans[0].cls)
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
        if self._formater:
            value = self._formater(self._addr, value)

        self._name = value

    def __init__(self, addr, format=None):
        global resolver

        if not isinstance(addr, compat.STRING_TYPES):
            raise TypeError('AddressResolve expects a valid IP address to resolve')

        self._addr = addr
        self._name = None
        self._formater = format

        if resolver:
            resolver.resolve(addr, self._resolve_cb)

    def __len__(self):
        return len(str(self))

    def resolveSucceed(self):
        if self._name:
            return True
        else:
            return False

    def __str__(self):
        if resolver:
            resolver.process()

        return self._name or self._addr


def process(timeout=0):
    global resolver

    if resolver:
        resolver.process(timeout)


def init():
    global resolver

    if env.dns_max_delay == -1:
        return

    if import_fail:
       env.log.warning(_("Asynchronous DNS resolution disabled: twisted.names and twisted.internet required: %s") % import_fail)
       return

    resolver = DNSResolver()
