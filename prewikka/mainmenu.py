# Copyright (C) 2015 CS-SI. All Rights Reserved.
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

from prewikka import view, template, localization
from prewikka.templates import MainMenu as MainMenuTemplate

from dateutil.relativedelta import relativedelta
import time, copy, datetime
from prewikka import utils, env


class MainMenuParameters(view.Parameters):
    allow_extra_parameters = False
    _INTERNAL_PARAMETERS = [ "timeline_value", "timeline_unit", "timeline_end", "timeline_start", "order_by", "timezone", "auto_apply_value", "auto_apply_enable"]

    def __init__(self, *args, **kwargs):
        env.hookmgr.declare_once("HOOK_MAINMENU_PARAMETERS_REGISTER", multi=True)
        env.hookmgr.declare_once("HOOK_MAINMENU_PARAMETERS_NORMALIZE", multi=True)
        env.hookmgr.declare_once("HOOK_MAINMENU_GET_CRITERIA", multi=True)
        env.hookmgr.declare_once("HOOK_MAINMENU_EXTRA_CONTENT", multi=True)

        # This will trigger register which in turn call a hook, do last
        view.Parameters.__init__(self, *args, **kwargs)

    def register(self):
        view.Parameters.register(self)

        self.optional("timeline_value", int, default=1, save=True)
        self.optional("timeline_unit", str, default="hour", save=True)
        self.optional("timeline_end", long)
        self.optional("timeline_start", long)
        self.optional("orderby", str, "time_desc", save=True)
        self.optional("timezone", str, "frontend_localtime", save=True)
        self.optional("auto_apply_value", str, default="1:00", save=True)
        self.optional("auto_apply_enable", str, default="false", save=True)

        for i in env.hookmgr.trigger("HOOK_MAINMENU_PARAMETERS_REGISTER", self):
            self._INTERNAL_PARAMETERS = self._INTERNAL_PARAMETERS + i

    def normalize(self, view_name, user):
        do_load = view.Parameters.normalize(self, view_name, user)

        if not self["timezone"] in ("frontend_localtime", "sensor_localtime", "utc"):
            raise view.InvalidValueError("timezone", self["timezone"])

        if self["orderby"] not in ("time_desc", "time_asc", "count_desc", "count_asc"):
            raise view.InvalidParameterValueError("orderby", self["orderby"])

        all(env.hookmgr.trigger("HOOK_MAINMENU_PARAMETERS_NORMALIZE", self, view_name, user))
        return do_load


class TimeUnit(object):
    _unit = ("year", "month", "day", "hour", "minute", "second")
    _dbunit = { "year": "year", "month": "month", "day": "mday", "hour": "hour", "minute": "min", "second": "sec" }

    @property
    def dbunit(self):
        return self._dbunit[str(self)]

    def __init__(self, unit):
        if isinstance(unit, int):
            assert(unit >= 0)
            self._idx = unit
        else:
            self._idx = self._unit.index(unit)

    def __add__(self, x):
        return TimeUnit(self._idx + x)

    def __sub__(self, x):
        return TimeUnit(self._idx - x)

    def __lt__(self, x):
        return int(self) > int(x)

    def __gt__(self, x):
        return int(self) < int(x)

    def __ge__(self, x):
        return int(self) <= int(x)

    def __le__(self, x):
        return int(self) >= int(x)

    def __eq__(self, x):
        return int(self) == int(x)

    def __int__(self):
        return self._idx

    def __str__(self):
        return self._unit[self._idx]


class MainMenuStep(object):
    def __init__(self, unit, value):
        d = { "year": (relativedelta(years=value), "%Y", "year"),
              "month": (relativedelta(months=value), "%m/%Y", "month"),
              "day": (relativedelta(days=value), "%m/%d/%Y", "mday"),
              "hour": (relativedelta(hours=value), "%m/%d/%Y %Hh", "hour"),
              "minute": (relativedelta(minutes=value), "%Hh%M", "min"),
        }

        self.unit = str(unit)
        self.timedelta, self.unit_format, self.dbunit = d[self.unit]


class MainMenu:
    def __init__(self, main_view):
        self.main = main_view
        self.dataset = template.PrewikkaTemplate(MainMenuTemplate.MainMenu)

    def _set_timeline_link(self, type, start, end):
        parameters = self.parameters - [ "offset" ] + { "timeline_start": int(time.mktime(start.timetuple())),
                                                        "timeline_end": int(time.mktime(end.timetuple())) }
        self.dataset["timeline.%s" % type] = utils.create_link(self.main.view_path, parameters)

    def _set_timeline(self, start, end):
        for unit in "minute", "hour", "day", "month", "year", "unlimited":
             self.dataset["timeline.%s_selected" % unit] = ""

        self.dataset["timeline.%s_selected" % self.parameters["timeline_unit"]] = "selected='selected'"

        if not start and not end:
            return

        self.dataset["timeline.start"] = localization.format_datetime(start, format="medium", tzinfo=self._tzobj)
        self.dataset["timeline.end"] = localization.format_datetime(end, format="medium", tzinfo=self._tzobj)
        self.dataset["timeline.current"] = utils.create_link(self.main.view_path, self.parameters - ["timeline_end"])

        timeunit = self.parameters["timeline_unit"]
        if timeunit != "unlimited":
            delta = relativedelta(**{timeunit + "s": self.parameters["timeline_value"]})
            self._set_timeline_link("next", end, end + delta)
            self._set_timeline_link("prev", start - delta, start)

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
            unit = TimeUnit("month") # step = month

        elif totsec > 24 * 60 * 60:
            unit = TimeUnit("day") # step = days

        elif totsec > 60 * 60:
            unit = TimeUnit("hour") # step = hours

        elif totsec > 60:
            unit = TimeUnit("minute") # step = minutes

        else:
            unit = TimeUnit("minute")

        return unit

    def _get_nearest_unit(self, stepno):
        delta = self.end - self.start
        totsec = delta.seconds + (delta.days * 24 * 60 * 60)

        gtable = { 365 * 24 * 60 * 60: "year",
                   31 * 24 * 60 * 60: "month",
                   24 * 60 * 60: "day",
                   60 * 60: "hour",
                   60: "minute" }

        nearest = min(gtable, key=lambda x:abs((totsec / x) - stepno))

        return TimeUnit(gtable[nearest])

    @staticmethod
    def _round_datetime(dtime, timeunit):
        d = {}

        tvaluelist = [ "year", "month", "day", "hour", "minute", "second", "microsecond" ]

        idx = tvaluelist.index(timeunit) + 1
        for i, unit in enumerate(tvaluelist[idx:]):
            d[unit] = 1 if idx + i <= 2 else 0 #months and days start from 1, hour/min/sec start from 0

        return dtime.replace(**d) + relativedelta(**{timeunit + "s": 1})

    def _setup_timeline_range(self):
        self.start = self.end = None
        if "timeline_start" in self.parameters:
            self.start = datetime.datetime.fromtimestamp(self.parameters["timeline_start"], utils.timeutil.tzlocal()).astimezone(self._tzobj)

        if "timeline_end" in self.parameters:
            self.end = datetime.datetime.fromtimestamp(self.parameters["timeline_end"], utils.timeutil.tzlocal()).astimezone(self._tzobj)

        self._timeunit, self._timevalue = self.parameters["timeline_unit"], self.parameters["timeline_value"]
        if self._timeunit == "unlimited":
            self._timeunit = "year"

        delta = relativedelta(**{self._timeunit + "s" if self._timeunit != "unlimited" else "years": self._timevalue})

        if self.start and not self.end:
            self.end = self.start + delta

        elif self.end and not self.start:
            self.start = self.end - delta

        elif self.start is None and self.end is None:
            self.start = self.end = datetime.datetime.now(self._tzobj)
            if self._timeunit in ("hour", "minute", "second"): #relative
                self.start = self.end - delta

            else: # absolute
                self.end = self._round_datetime(self.end, self._timeunit)
                if self.parameters["timeline_unit"] == "unlimited":
                    self.start = datetime.datetime(1970, 1, 1, tzinfo=utils.timeutil.tzutc()).astimezone(self._tzobj)
                else:
                    self.start = self.end - delta

    def _setup_timezone(self):
        for timezone, tzobj, tzname in (("utc", utils.timeutil.tzutc, "UTC"),
                                        ("sensor_localtime", utils.timeutil.tzlocal, _("localtime")),
                                        ("frontend_localtime", utils.timeutil.tzlocal, _("localtime"))):
            if timezone == self.parameters["timezone"]:
                self._tzobj = tzobj()
                self.dataset["timeline.range_timezone"] = tzname
                self.dataset["timeline.%s_selected" % timezone] = "selected='selected'"
            else:
                self.dataset["timeline.%s_selected" % timezone] = ""

    def get_criteria(self, ctype="alert"):
        criteria = []

        for c in env.hookmgr.trigger("HOOK_MAINMENU_GET_CRITERIA", self, ctype):
            if c:
                criteria.append(c)

        if self.start:
                criteria.append("%s.create_time >= '%s'" % (ctype, str(self.start)))

        if self.end:
                criteria.append("%s.create_time <= '%s'" % (ctype, str(self.end)))

        return " && ".join(criteria)

    def get_step(self, stepno=None):
        if stepno:
            x = self._get_nearest_unit(stepno)
        else:
            x = self._get_unit()

        return MainMenuStep(x, 1)

    def get_parameters(self):
        return dict(((key, self.parameters[key]) for key in self.parameters._INTERNAL_PARAMETERS if key in self.parameters))

    def render(self, parameters):
        self.parameters = parameters
        self._setup_timezone()
        self._setup_timeline_range()

        for t in "time_desc", "time_asc", "count_desc", "count_asc":
            self.dataset["timeline.%s_selected" % t] = ""

        self.dataset["timeline.%s_selected" % parameters["orderby"]] = "selected='selected'"

        for unit in "min", "hour", "day", "month", "year", "unlimited":
            self.dataset["timeline.%s_selected" % unit] = ""

        self.dataset["timeline.value"] = parameters["timeline_value"]
        self.dataset["timeline.%s_selected" % parameters["timeline_unit"]] = "selected='selected'"

        self._set_timeline(self.start, self.end)

        self.dataset["auto_apply_value"] = self.parameters["auto_apply_value"]
        self.dataset["auto_apply_enable"] = self.parameters["auto_apply_enable"]

        self.dataset["menu_extra"] = env.hookmgr.trigger("HOOK_MAINMENU_EXTRA_CONTENT", self, self._criteria_type)

        self.dataset.update(parameters)


class MainMenuAlert(MainMenu):
    def __init__(self, main_view):
        MainMenu.__init__(self, main_view)
        self._criteria_type = "alert"

class MainMenuHeartbeat(MainMenu):
    def __init__(self, main_view):
        MainMenu.__init__(self, main_view)
        self._criteria_type = "heartbeat"
