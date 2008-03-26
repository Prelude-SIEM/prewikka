#!/usr/bin/python

import time
import socket

dns_resolve = True

try:
    from twisted.internet import reactor
    from twisted.names import client, dns, hosts, cache, resolve
except:
    dns_resolve = False
    pass

def ip_reverse(addr):
    try:
        parts = list(socket.inet_pton(socket.AF_INET6, addr).encode('hex_codec'))
        origin = ".ip6.arpa"
    except:
        parts = ["%d" % ord(byte) for byte in socket.inet_aton(addr)]
        origin = ".in-addr.arpa"

    parts.reverse()
    return '.'.join(parts) + origin


class DNSResolve:
    def __init__(self):
        self._query = 0
        self._cache = cache.CacheResolver(verbose=10)
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

    def process(self, timeout=0):            
	end = now = time.time()
	final = now + timeout

        while self._query > 0:
	    reactor.runUntilCurrent();
	    reactor.doIteration(timeout)

	    end = time.time()
            if end >= final:
                break

	#print "max=%f elapsed:%f" % (timeout, end-now)
	
    def resolve(self, addr, resolve_cb):
	try:	
	    addr = ip_reverse(addr)
	except:
	    return

	self._query += 1
	self._resolve.lookupPointer(addr).addCallback(self._resolve_cb, addr, resolve_cb).addErrback(self._error_cb)
	self.process()


if dns_resolve:
    resolver = DNSResolve()

class AddressResolve:
    def _resolve_cb(self, value):
	self._name = value
	
    def __init__(self, addr):
	self._addr = addr
	self._name = None

        if dns_resolve:
	    resolver.resolve(addr, self._resolve_cb)

    def __len__(self):
	return len(str(self))

    def __str__(self):
        if dns_resolve:
	    resolver.process()

	return self._name or self._addr

    def __repr__(self):
	return str(self)


    def isResolved(self):
	resolver.process()
			
	if self._name:
	    return True
	
	return False
	
