# -*- coding: utf-8 -*-
# Copyright (C) 2016-2020 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
# Author: François POIROTTE <francois.poirotte@c-s.fr>
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

from datetime import datetime

from prewikka import error, utils


def _get_yday(date):
    return date.timetuple().tm_yday


_EXTRACT_TO_DATETIME = {
    "year": "year",
    "month": "month",
    "yday": _get_yday,
    "mday": "day",
    "wday": datetime.weekday,
    "hour": "hour",
    "min": "minute",
    "sec": "second"
}


def extract_from_date(date, extract):
    """Extracts and returns the value of a specified datetime field
       from a datetime.
    """
    if not isinstance(date, datetime):
        raise error.PrewikkaUserError(N_("Invalid operation"),
                                      N_("Extraction is supported only for date fields"))

    attr = _EXTRACT_TO_DATETIME[extract]
    return attr(date) if callable(attr) else getattr(date, attr)


def apply_timezone(date, tz):
    """Returns a datetime object which is equivalent to the given
       datetime converted to the given timezone.
    """
    if not date.tzinfo or (date.tzinfo and date.tzinfo.utcoffset(date) is None):
        # date is a naive datetime
        date = date.replace(tzinfo=utils.timeutil.tzutc())

    return date.astimezone(tz)
