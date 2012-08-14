# coding=UTF-8
# Copyright (C) 2007-2012 CS-SI. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import locale, gettext, __builtin__, time
from prewikka import siteconfig, utils, Config

try:
    from threading import local, Lock
except ImportError:
    # copy of _thread_local.py from python 2.5
    from dummy_threading import Lock
    from prewikka._threading_local import local


_lock = Lock()
_DEFAULT_LANGUAGE = Config.Config(siteconfig.conf_dir + "/prewikka.conf").general.getOptionValue("default_locale", "en_GB")
_localized_thread = local()
_all_locale = { }


def _safeGettext(s):
    try:
        return utils.toUnicode(_localized_thread.data.gettext(s))
    except:
        return s

def _safeNgettext(singular, plural, num):
    try:
        return utils.toUnicode(_localized_thread.data.ngettext(singular, plural, num))
    except:
        if num <= 1:
            return singular
        else:
            return plural

def _deferredGettext(s):
    return s

gettext.install("prewikka", siteconfig.locale_dir)
__builtin__._ = _safeGettext
__builtin__.N_ = _deferredGettext
__builtin__.ngettext = _safeNgettext

_LANGUAGES = {
               "Deutsch": "de_DE",
               u"Español": "es_ES",
               "English": "en_GB",
               u"Français": "fr_FR",
	       "Italiano": "it_IT",
               "Polski": "pl_PL",
               u"Português (Brasileiro)": "pt_BR",
               u"Русский": "ru_RU"
             }


def setLocale(lang):
    if not lang:
        lang = _DEFAULT_LANGUAGE

    locale.setlocale(locale.LC_ALL, lang.encode('utf8'))

    _lock.acquire()

    if not _all_locale.has_key(lang):
        _all_locale[lang] = gettext.translation("prewikka", siteconfig.locale_dir, languages=[lang])

    _lock.release()
    _localized_thread.data = _all_locale[lang]


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
    try:
        return _localized_thread.data.charset()
    except:
        return "iso-8859-1"

def getDate():
    _localized_month = [ _("January"),
                         _("February"),
                         _("March"),
                         _("April"),
                         _("May"),
                         _("June"),
                         _("July"),
                         _("August"),
                         _("September"),
                         _("November"),
                         _("October"),
                         _("December") ]

    _localized_weekday = [ _("Monday"),
                           _("Tuesday"),
                           _("Wednesday"),
                           _("Thursday"),
                           _("Friday"),
                           _("Saturday"),
                           _("Sunday") ]

    weekday, day, month, year = utils.toUnicode(time.strftime("%A %d %B %Y")).split()
    return u" ".join((_(weekday).lower(), day, _(month).lower(), year))
