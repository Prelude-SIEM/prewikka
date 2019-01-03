# Copyright (C) 2018-2019 CS-SI. All Rights Reserved.
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

"""
Tests for `prewikka.resolve`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.resolve import AddressResolve, process, init


@pytest.mark.xfail(reason='Issue #2544')
def test_address_resolve_ipv4():
    """
    Test `prewikka.resolve.AddressResolve` for IPv4.

    NOTE: values could change if provider change IP/domain name.
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    fail_ipv4 = '127.0.13.37'
    success_ipv4 = '208.67.222.222'
    success_domain_ipv4 = 'resolver1.opendns.com'

    res = AddressResolve(fail_ipv4)

    assert str(res) == fail_ipv4
    assert not res.resolveSucceed()

    res = AddressResolve(success_ipv4)

    assert str(res) == success_domain_ipv4
    assert str(len(res)) != 0  # exact value could change function of server used, we check if no null only
    assert res.resolveSucceed()

    # invalid IP

    with pytest.raises(TypeError):
        AddressResolve(42)


@pytest.mark.xfail(reason='Issue #2544')
def test_address_resolve_ipv6():
    """
    Test `prewikka.resolve.AddressResolve` for IPv6.

    NOTE: values could change if provider change IP/domain name.
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    success_ipv6 = '2620:0:ccc::2'
    success_ipv6_full = '2620:0000:0ccc:0000:0000:0000:0000:0002'
    success_domain_ipv6 = 'resolver1.ipv6-sandbox.opendns.com'

    assert str(AddressResolve(success_ipv6)) == success_domain_ipv6
    assert str(AddressResolve(success_ipv6_full)) == success_domain_ipv6


def test_address_resolve():
    """
    Test `prewikka.resolve.AddressResolve` class.

    Test methods of the class AddressResolve (resolve() method is tested in dedicated tests).
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    process()

    # change env.dns_max_delay
    backup_env_max_delay = env.dns_max_delay

    env.dns_max_delay = -1

    assert not init()

    # clean
    env.dns_max_delay = backup_env_max_delay
