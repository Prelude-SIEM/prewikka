# coding=UTF-8
# Copyright (C) 2007-2016 CS-SI. All Rights Reserved.
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

import prelude
import pkg_resources, locale, gettext, __builtin__, datetime, pytz
from prewikka import utils, env, log

from threading import local, Lock

# Babel functions
import babel.dates, babel.numbers, babel.core

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
        self._domains = utils.OrderedDict([("prewikka", pkg_resources.resource_filename(__name__, "locale"))])

    def addDomain(self, domain, locale_dir):
        with self._domains_lock:
            self._domains[domain] = locale_dir

    def _getCatalog(self, domain, lang):
        with self._catalogs_lock:
            if not domain in self._catalogs:
                self._catalogs[domain] = {}

            if not lang in self._catalogs[domain]:
                logger.info("loading '%s' translation for domain '%s'", lang, domain)
                self._catalogs[domain][lang] = gettext.translation(domain, self._domains[domain], languages=[lang])

            return self._catalogs[domain][lang]

    def getCharset(self):
        try:
           return self._data.catalog.charset()
        except:
           return env.config.default_encoding

    def getLocale(self):
        try:
            return self._data.lang
        except:
            return env.config.default_locale

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
        return self._data.catalog.gettext(s) if hasattr(self._data, "catalog") else s

    def dgettext(self, domain, s):
        if not hasattr(self._data, "catalog"):
                return s

        if s in self._data.catalog:
                return self._data.catalog.dgettext(domain, s)

        return self._data.catalog.gettext(s)

    def ngettext(self, singular, plural, num):
        if not hasattr(self._data, "catalog"):
            return singular if num <= 1 else plural

        return self._data.catalog.ngettext(singular, plural, num)

    def dngettext(self, domain, singular, plural, num):
        if hasattr(self._data, "catalog"):
            return singular if num <= 1 else plural

        return self._data.catalog.ngettext(domain, singular, plural, num)

translation = TranslationProxy()

def _deferredGettext(s):
    return s

__builtin__._ = translation.gettext
__builtin__.N_ = _deferredGettext
__builtin__.ngettext = translation.ngettext


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
        lang = env.config.default_locale

    translation.setLocale("%s.%s" % (lang, env.config.default_encoding))


def getLanguages():
    l = _LANGUAGES.keys()
    l.sort()
    return l

def getLanguagesIdentifiers():
    return _LANGUAGES.values()


def getLanguagesAndIdentifiers():
    l = _LANGUAGES.keys()
    l.sort()
    return [ (_(x), _LANGUAGES[x]) for x in l ]


def getCurrentCharset():
    return translation.getCharset()

def format_date(date=None, tzinfo=None, **kwargs):
    if isinstance(date, (float, int)):
        date = datetime.datetime.utcfromtimestamp(date).replace(tzinfo=utils.timeutil.tzutc())

    # Babel format_date() miss tzinfo convertion
    if date:
        date = date.astimezone(tzinfo or env.request.user.timezone)

    return babel.dates.format_date(date, locale=translation.getLocale(), **kwargs).encode(getCurrentCharset())

def format_time(dt=None, tzinfo=None, **kwargs):
    if isinstance(dt, (float, int, prelude.IDMEFTime)):
        dt = datetime.datetime.fromtimestamp(dt, utils.timeutil.tzutc())

    if not tzinfo:
        tzinfo = env.request.user.timezone

    return babel.dates.format_time(dt, tzinfo=tzinfo, locale=translation.getLocale(), **kwargs).encode(getCurrentCharset())

def format_datetime(dt=None, tzinfo=None, **kwargs):
    if isinstance(dt, (float, int, prelude.IDMEFTime)):
        dt = datetime.datetime.fromtimestamp(dt, utils.timeutil.tzutc())

    if not tzinfo:
        tzinfo = env.request.user.timezone

    return babel.dates.format_datetime(datetime=dt, tzinfo=tzinfo, locale=translation.getLocale(), **kwargs).encode(getCurrentCharset())

def format_timedelta(*args, **kwargs):
    return _format_timedelta(*args, locale=translation.getLocale(), **kwargs).encode(getCurrentCharset())

def format_number(*args, **kwargs):
    return babel.numbers.format_number(*args, locale=translation.getLocale(), **kwargs).encode(getCurrentCharset())


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
    return sorted(zone for zone in babel.core.get_global('zone_territories').keys() + ["UTC"] if not zone.startswith('Etc/'))

def get_system_timezone():
    try:
        return babel.dates.LOCALTZ.zone
    except:
        return "UTC"
