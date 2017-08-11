# coding=UTF-8
# Copyright (C) 2007-2017 CS-SI. All Rights Reserved.
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

import collections
import datetime
import gettext
import sys
from threading import Lock, local

import babel.core
# Babel functions
import babel.dates
import babel.numbers
import pkg_resources
import prelude
from prewikka import log, utils

if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins

try:
    from babel.dates import format_timedelta as _format_timedelta
except ImportError:
    from prewikka.compat.babelcompat import format_timedelta as _format_timedelta


logger = log.getLogger(__name__)


class TranslationProxy(object):
    def __init__(self):
        self._data = local()
        self._catalogs = {}
        self._catalogs_lock = Lock()

        self._domains_lock = Lock()
        self._domains = collections.OrderedDict([("prewikka", pkg_resources.resource_filename(__name__, "locale"))])

    def addDomain(self, domain, locale_dir):
        with self._domains_lock:
            self._domains[domain] = locale_dir

    def _getCatalog(self, domain, lang):
        with self._catalogs_lock:
            if domain not in self._catalogs:
                self._catalogs[domain] = {}

            if lang not in self._catalogs[domain]:
                logger.info("loading '%s' translation for domain '%s'", lang, domain)
                self._catalogs[domain][lang] = gettext.translation(domain, self._domains[domain], languages=[lang])

            return self._catalogs[domain][lang]

    def getCharset(self):
        try:
            return self._data.catalog.charset()
        except:
            return env.config.general.encoding

    def getLocale(self):
        try:
            return self._data.lang
        except:
            return env.config.general.default_locale

    def setLocale(self, lang):
        first = None
        for domain, locale_dir in self._domains.items():
                t = self._getCatalog(domain, lang)
                if not first:
                    first = t
                else:
                    first._catalog.update(t._catalog)

        self._data.lang = lang
        self._data.catalog = first

    def gettext(self, s):
        if sys.version_info < (3, 0):
            return self._data.catalog.ugettext(s) if hasattr(self._data, "catalog") else s
        else:
            return self._data.catalog.gettext(s) if hasattr(self._data, "catalog") else s

    def ngettext(self, singular, plural, num):
        if not hasattr(self._data, "catalog"):
            return singular if num <= 1 else plural

        if sys.version_info < (3, 0):
            return self._data.catalog.ungettext(singular, plural, num)
        else:
            return self._data.catalog.ngettext(singular, plural, num)


translation = TranslationProxy()


class _DeferredGettext(text_type):
    def __new__(cls, text, arguments=None):
        message = text % arguments if arguments else text
        o = text_type.__new__(cls, message)
        o.origin = text
        o._arguments = arguments
        return o

    def translate(self):
        s = translation.gettext(self.origin)
        return s % self._arguments if self._arguments else s


def _translate(s):
    if isinstance(s, _DeferredGettext):
        return s.translate()
    else:
        return translation.gettext(s)


builtins._ = _translate
builtins.N_ = _DeferredGettext
builtins.ngettext = translation.ngettext

DATE_YM_FMT = N_("%m/%Y")
DATE_YMD_FMT = N_("%m/%d/%Y")
DATE_YMDH_FMT = N_("%m/%d/%Y %Hh")
DATE_YMDHM_FMT = N_("%m/%d/%Y %H:%M")
DATE_YMDHMS_FMT = N_("%m/%d/%Y %H:%M:%S")

TIME_HM_FMT = N_("%H:%M")
TIME_HMS_FMT = N_("%H:%M:%S")


_LANGUAGES = {
    "Deutsch": "de_DE",
    "Español": "es_ES",
    "English": "en_GB",
    "Français": "fr_FR",
    "Italiano": "it_IT",
    "Polski": "pl_PL",
    "Português (Brasileiro)": "pt_BR",
    "Русский": "ru_RU"
}


def setLocale(lang):
    if not lang:
        lang = env.config.general.default_locale

    translation.setLocale("%s.%s" % (lang, env.config.general.encoding))


def getLanguages():
    return sorted(_LANGUAGES)


def getLanguagesIdentifiers():
    return _LANGUAGES.values()


def getLanguagesAndIdentifiers():
    return [(_(x), _LANGUAGES[x]) for x in sorted(_LANGUAGES)]


def getCurrentCharset():
    return translation.getCharset()


def format_date(date=None, tzinfo=None, **kwargs):
    if isinstance(date, (float, int)):
        date = datetime.datetime.utcfromtimestamp(date).replace(tzinfo=utils.timeutil.tzutc())

    # Babel format_date() miss tzinfo convertion
    if date:
        date = date.astimezone(tzinfo or env.request.user.timezone)

    return babel.dates.format_date(date, locale=translation.getLocale(), **kwargs)


def format_time(dt=None, tzinfo=None, **kwargs):
    if isinstance(dt, (float, int, prelude.IDMEFTime)):
        dt = datetime.datetime.fromtimestamp(dt, utils.timeutil.tzutc())

    if not tzinfo:
        tzinfo = env.request.user.timezone

    return babel.dates.format_time(dt, tzinfo=tzinfo, locale=translation.getLocale(), **kwargs)


def format_datetime(dt=None, tzinfo=None, **kwargs):
    if isinstance(dt, (float, int, prelude.IDMEFTime)):
        dt = datetime.datetime.fromtimestamp(dt, utils.timeutil.tzutc())

    if not tzinfo:
        tzinfo = env.request.user.timezone

    return babel.dates.format_datetime(datetime=dt, tzinfo=tzinfo, locale=translation.getLocale(), **kwargs)


def format_timedelta(*args, **kwargs):
    return _format_timedelta(*args, locale=translation.getLocale(), **kwargs)


def format_number(*args, **kwargs):
    return babel.numbers.format_number(*args, locale=translation.getLocale(), **kwargs)


def get_period_names(*args, **kwargs):
    return babel.dates.get_period_names(*args, locale=translation.getLocale(), **kwargs)


def get_day_names(*args, **kwargs):
    return babel.dates.get_day_names(*args, locale=translation.getLocale(), **kwargs)


def get_month_names(*args, **kwargs):
    return babel.dates.get_month_names(*args, locale=translation.getLocale(), **kwargs)


def get_quarter_names(*args, **kwargs):
    return babel.dates.get_quarter_names(*args, locale=translation.getLocale(), **kwargs)


def get_era_names(*args, **kwargs):
    return babel.dates.get_era_names(*args, locale=translation.getLocale(), **kwargs)


def get_calendar_format():
    """ Return a date format for use by jquery's datetime picker """

    calendar_format = babel.dates.get_date_format(
        'short',
        translation.getLocale()).pattern

    # babel uses 'MM' for month, and jquery uses 'mm'
    # 4-digits year: "yyyy" in Babel, "yy" in jQuery.
    # 2-digits year: "yy" in Babel, "y" in jQuery.
    return calendar_format.replace("yy", "y").replace("MM", "mm")


def get_timezones():
    return sorted(zone for zone in list(babel.core.get_global('zone_territories').keys()) + ["UTC"] if not zone.startswith('Etc/'))


def get_system_timezone():
    try:
        return babel.dates.LOCALTZ.zone
    except:
        return "UTC"
