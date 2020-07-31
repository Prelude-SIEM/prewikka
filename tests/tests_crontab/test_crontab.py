# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.crontab`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import gevent

from datetime import datetime, timedelta
from pytz import timezone

import pytest

from prewikka.crontab import CronJob, crontab


def cronjob_test_func():
    """
    Function for tests only.
    """
    return 42


def cronjob_test_func_exception():
    """
    Function for tests only.
    """
    raise Exception


def test_crontab():
    """
    Test `prewikka.crontab.Crontab` class.
    """
    cron_name = 'test_name'
    cron_schedule = '*/1 * * * *'

    # list()
    crontab_count = len(list(crontab.list()))

    assert crontab_count == 3

    # add()
    crontab.add(cron_name, cron_schedule, user=env.request.user, ext_type=None, ext_id=None, enabled=True)

    assert len(list(crontab.list())) == crontab_count + 1

    test_crontab = next(crontab.list())

    # get()
    assert crontab.get(test_crontab.id).id == test_crontab.id

    # update()
    crontab.update(test_crontab.id, schedule='*/2 * * * *')

    assert len(list(crontab.list())) == crontab_count + 1
    assert crontab.get(test_crontab.id).id == test_crontab.id
    assert crontab.get(test_crontab.id).schedule == '*/2 * * * *'

    assert len(list(crontab.list())) == crontab_count + 1

    # delete()
    assert len(list(crontab.list())) == crontab_count + 1

    crontab.delete(**{'id': test_crontab.id})

    assert len(list(crontab.list())) == crontab_count

    crontab.delete(**{'id': test_crontab.id})

    assert len(list(crontab.list())) == crontab_count

    crontab.add(cron_name+'2', cron_schedule, user=env.request.user, ext_type='foo')
    crontab.add(cron_name+'3', cron_schedule, user=env.request.user, ext_type='foo', ext_id=1)
    crontab.add(cron_name+'4', cron_schedule, user=env.request.user, enabled=False)

    # clean
    env.db.query('DELETE FROM Prewikka_Crontab')


def test_cronjob():
    """
    Test `prewikka.crontab.CronJob` class.
    """
    now = datetime.now(timezone("UTC"))

    cron_name = 'test_name'
    cron_schedule = '* * * * *'
    cron_base = now.replace(second=0, microsecond=0)
    cron_runcnt = 0

    # create a crontab for tests
    cron_id = crontab.add(cron_name, cron_schedule, user=env.request.user, ext_type=None, ext_id=None, enabled=True)

    cronjob = CronJob(cron_id,
                      cron_name,
                      cron_schedule,
                      cronjob_test_func,
                      cron_base - timedelta(minutes=33),
                      cron_runcnt,
                      user=env.request.user)

    # replace() needed for croniter < 0.3.8
    assert now - timedelta(minutes=1) < cronjob.next_schedule.replace(microsecond=0) < now

    cronjob = CronJob(cron_id,
                      cron_name,
                      cron_schedule,
                      cronjob_test_func,
                      cron_base,
                      cron_runcnt,
                      user=env.request.user)

    # replace() needed for croniter < 0.3.8
    assert now < cronjob.next_schedule.replace(microsecond=0) < now + timedelta(minutes=1)

    # run()
    query = env.db.query("SELECT id, runcnt FROM Prewikka_Crontab WHERE id=%d", cron_id)

    assert len(query) == 1

    runcnt = int(query[0][1])
    cronjob.run(now + timedelta(minutes=1))
    gevent.sleep(1)
    query = env.db.query("SELECT id, runcnt FROM Prewikka_Crontab WHERE id=%d", cron_id)

    assert len(query) == 1
    assert int(query[0][1]) == runcnt+1

    cronjob.run(now + timedelta(minutes=1))
    gevent.sleep(1)
    query = env.db.query("SELECT id, runcnt FROM Prewikka_Crontab WHERE id=%d", cron_id)

    assert len(query) == 1
    assert int(query[0][1]) == runcnt+1

    with pytest.raises(Exception):
        CronJob(cron_id,
                cron_name,
                cron_schedule,
                cronjob_test_func_exception(),
                cron_base,
                cron_runcnt,
                user=env.request.user)

    # clean
    env.db.query('DELETE FROM Prewikka_Crontab')
