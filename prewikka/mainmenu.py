# Copyright (C) 2015-2017 CS-SI. All Rights Reserved.
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

import calendar
import datetime
import functools

from dateutil.relativedelta import relativedelta
from prewikka import hookmanager, localization, template, utils, view
from prewikka.dataprovider import Criterion

_MAINMENU_TEMPLATE = template.PrewikkaTemplate(__name__, "templates/mainmenu.mak")


class MainMenuParameters(view.Parameters):
    _INTERNAL_PARAMETERS = ["timeline_value", "timeline_unit", "timeline_end", "timeline_start", "timeline_absolute",
                            "order_by", "timezone", "auto_apply_value"]

    def __init__(self, *args, **kwargs):
        # This will trigger register which in turn call a hook, do last
        view.Parameters.__init__(self, *args, **kwargs)

    def register(self):
        view.Parameters.register(self)

        self.optional("timeline_value", int, default=1, save=True, general=True)
        self.optional("timeline_unit", text_type, default="month", save=True, general=True)
        self.optional("timeline_absolute", int, default=0, save=True, general=True)
        self.optional("timeline_end", int, save=True, general=True)
        self.optional("timeline_start", int, save=True, general=True)
        self.optional("orderby", text_type, "time_desc")
        self.optional("auto_apply_value", int, default=0, save=True, general=True)

        for i in hookmanager.trigger("HOOK_MAINMENU_PARAMETERS_REGISTER", self):
            self._INTERNAL_PARAMETERS = self._INTERNAL_PARAMETERS + i

    def normalize(self, view_name, user):
        do_load = view.Parameters.normalize(self, view_name, user)

        if self["orderby"] not in ("time_desc", "time_asc", "count_desc", "count_asc"):
            raise view.InvalidParameterValueError("orderby", self["orderby"])

        all(hookmanager.trigger("HOOK_MAINMENU_PARAMETERS_NORMALIZE", self))
        return do_load


class TimeUnit(object):
    _unit = ("year", "month", "day", "hour", "minute", "second")
    _dbunit = {"year": "year", "month": "month", "day": "mday", "hour": "hour", "minute": "min", "second": "sec"}

    @property
    def dbunit(self):
        return self._dbunit[text_type(self)]

    def __init__(self, unit):
        if isinstance(unit, int):
            assert 0 <= unit < len(self._unit)
            self._idx = unit
        else:
            assert unit in self._unit
            self._idx = self._unit.index(unit)

    def __add__(self, x):
        return TimeUnit(self._idx + x)

    def __sub__(self, x):
        return TimeUnit(self._idx - x)

    def __lt__(self, x):
        if isinstance(x, TimeUnit):
            return int(self) > int(x)
        else:
            return int(self) < x

    def __gt__(self, x):
        if isinstance(x, TimeUnit):
            return int(self) < int(x)
        else:
            return int(self) > x

    def __ge__(self, x):
        if isinstance(x, TimeUnit):
            return int(self) <= int(x)
        else:
            return int(self) >= x

    def __le__(self, x):
        if isinstance(x, TimeUnit):
            return int(self) >= int(x)
        else:
            return int(self) <= x

    def __eq__(self, x):
        return int(self) == int(x)

    def __int__(self):
        return self._idx

    def __str__(self):
        return self._unit[self._idx]


class MainMenuStep(object):
    def __init__(self, unit, value):
        d = {
            "year": (relativedelta(years=value), "%Y", "year"),
            "month": (relativedelta(months=value), _(localization.DATE_YM_FMT), "month"),
            "day": (relativedelta(days=value), _(localization.DATE_YMD_FMT), "mday"),
            "hour": (relativedelta(hours=value), _(localization.DATE_YMDH_FMT), "hour"),
            "minute": (relativedelta(minutes=value), _(localization.TIME_HM_FMT), "min"),
        }

        self.unit = text_type(unit)
        self.timedelta, self.unit_format, self.dbunit = d[self.unit]


class MainMenu(object):
    def __init__(self, criteria_type=None, **kwargs):
        if kwargs.get("inline", True):
            env.request.menu = self

        self._criteria_type = criteria_type
        self.dataset = _MAINMENU_TEMPLATE.dataset(inline=True, period=True, refresh=True, label_width=2, input_size="md")
        self.dataset.update(kwargs)

        self.dataset["timeline"] = utils.AttrObj()
        self.dataset["timeline"].quick = [
            (_("Today"), 1, "day", 1),
            (_("This month"), 1, "month", 1),
            (ngettext("%d hour", "%d hours", 1) % 1, 1, "hour", 0),
            (ngettext("%d hour", "%d hours", 2) % 2, 2, "hour", 0),
            (ngettext("%d day", "%d days", 1) % 1, 1, "day", 0),
            (ngettext("%d day", "%d days", 2) % 2, 2, "day", 0),
            (ngettext("%d week", "%d weeks", 1) % 1, 1, "week", 0),
            (ngettext("%d month", "%d months", 1) % 1, 1, "month", 0),
            (ngettext("%d month", "%d months", 3) % 3, 3, "month", 0),
            (ngettext("%d year", "%d years", 1) % 1, 1, "year", 0)]

        self.dataset["timeline"].refresh = [
            (ngettext("%d second", "%d seconds", 30) % 30, 30),
            (ngettext("%d minute", "%d minutes", 1) % 1, 60),
            (ngettext("%d minute", "%d minutes", 5) % 5, 60*5),
            (ngettext("%d minute", "%d minutes", 10) % 10, 60*10)]

        self._render()

    def _set_timeline(self, start, end):
        for unit in "minute", "hour", "day", "month", "year", "unlimited":
            setattr(self.dataset["timeline"], "%s_selected" % unit, "")

        setattr(self.dataset["timeline"], "%s_selected" % env.request.parameters["timeline_unit"], "selected='selected'")

        if not start and not end:
            return

        self.dataset["timeline"].start = start.replace(tzinfo=None).isoformat()
        self.dataset["timeline"].end = end.replace(tzinfo=None).isoformat()

    def _get_unit(self):
        delta = self.end - self.start
        totsec = delta.seconds + (delta.days * 24 * 60 * 60)

        if self._timeunit != "unlimited" and self._timevalue > 1:
            unit = TimeUnit(self._timeunit)
            if int(unit) > 0:
                unit = unit - 1

        elif totsec > 365 * 24 * 60 * 60:
            unit = TimeUnit("year")

        elif totsec > 30 * 24 * 60 * 60:
            unit = TimeUnit("month")  # step = month

        elif totsec > 24 * 60 * 60:
            unit = TimeUnit("day")  # step = days

        elif totsec > 60 * 60:
            unit = TimeUnit("hour")  # step = hours

        elif totsec > 60:
            unit = TimeUnit("minute")  # step = minutes

        else:
            unit = TimeUnit("minute")

        return unit

    def _get_nearest_unit(self, stepno):
        delta = self.end - self.start
        totsec = delta.seconds + (delta.days * 24 * 60 * 60)

        if totsec < 60:
            return TimeUnit("minute")

        gtable = {
            365 * 24 * 60 * 60: "year",
            31 * 24 * 60 * 60: "month",
            24 * 60 * 60: "day",
            60 * 60: "hour",
            60: "minute"
        }

        nearest = min(gtable, key=lambda x: abs((totsec / x) - stepno))

        return TimeUnit(gtable[nearest])

    def _setup_timeline_range(self):
        self.start = self.end = None
        if "timeline_start" in env.request.parameters:
            self.start = env.request.user.timezone.localize(datetime.datetime.utcfromtimestamp(env.request.parameters["timeline_start"]))

        if "timeline_end" in env.request.parameters:
            self.end = env.request.user.timezone.localize(datetime.datetime.utcfromtimestamp(env.request.parameters["timeline_end"]))

        self._timeunit, self._timevalue = env.request.parameters["timeline_unit"], env.request.parameters["timeline_value"]
        if self._timeunit == "unlimited":
            self._timeunit = "year"

        delta = relativedelta(**{self._timeunit + "s" if self._timeunit != "unlimited" else "years": self._timevalue})

        if self.start and not self.end:
            self.end = datetime.datetime.now(env.request.user.timezone).replace(microsecond=0)

        elif self.end and not self.start:
            self.start = self.end - delta

        elif self.start is None and self.end is None:
            self.start = self.end = datetime.datetime.now(env.request.user.timezone).replace(microsecond=0)
            if not env.request.parameters["timeline_absolute"]:  # relative
                self.start = self.end - delta

            else:  # absolute
                self.end = utils.timeutil.truncate(self.end, self._timeunit) + relativedelta(**{self._timeunit + "s": 1})
                if env.request.parameters["timeline_unit"] == "unlimited":
                    self.start = datetime.datetime.fromtimestamp(0).replace(tzinfo=env.request.user.timezone)
                else:
                    self.start = self.end - delta

                self.end += relativedelta(seconds=-1)

    @staticmethod
    def mktime_param(dt, precision=None):
        tpl = list(dt.timetuple())

        if precision is not None:
            assert(precision > 0)
            for i in range(precision, len(tpl)):
                # month/day must at least be 1
                tpl[i] = 1 if i <= 2 else 0

        return int(calendar.timegm(tpl))

    def get_criteria(self):
        criteria = Criterion()

        if self.start:
            start = self.start.astimezone(utils.timeutil.timezone("UTC"))
            criteria += Criterion("{backend}.{time_field}", ">=", start)

        if self.end:
            end = self.end.astimezone(utils.timeutil.timezone("UTC"))
            criteria += Criterion("{backend}.{time_field}", "<=", end)

        return criteria

    def get_step(self, stepno=None):
        if stepno:
            x = self._get_nearest_unit(stepno)
        else:
            x = self._get_unit()

        return MainMenuStep(x, 1)

    def get_parameters(self):
        return dict(((key, env.request.parameters[key]) for key in env.request.parameters._INTERNAL_PARAMETERS if key in env.request.parameters))

    def _render(self):
        self.dataset["timeline"].order_by = env.request.parameters["orderby"]
        self.dataset["timeline"].value = env.request.parameters["timeline_value"]
        self.dataset["timeline"].unit = env.request.parameters["timeline_unit"]
        self.dataset["timeline"].absolute = env.request.parameters["timeline_absolute"]
        self.dataset["timeline"].quick_selected = _("Custom")
        self.dataset["timeline"].quick_custom = True
        self.dataset["timeline"].refresh_selected = _("Inactive")
        self.dataset["auto_apply_value"] = env.request.parameters["auto_apply_value"]
        self.dataset["timeline"].time_format = localization.get_calendar_format()

        for label, value in self.dataset["timeline"].refresh:
            if value == env.request.parameters["auto_apply_value"]:
                self.dataset["timeline"].refresh_selected = label

        if "timeline_start" not in env.request.parameters and "timeline_end" not in env.request.parameters:
            for label, value, unit, absolute in self.dataset["timeline"].quick:
                if value == env.request.parameters["timeline_value"] and unit == env.request.parameters["timeline_unit"] and absolute == env.request.parameters["timeline_absolute"]:
                    self.dataset["timeline"].quick_selected = label
                    self.dataset["timeline"].quick_custom = False
                    break

        self._setup_timeline_range()
        self._set_timeline(self.start, self.end)

        self.dataset["menu_extra"] = filter(None, hookmanager.trigger("HOOK_MAINMENU_EXTRA_CONTENT", self._criteria_type))


def MainMenuType(criteria_type):
    return functools.partial(MainMenu, criteria_type=criteria_type)


MainMenuAlert = MainMenuType("alert")
MainMenuHeartbeat = MainMenuType("heartbeat")
