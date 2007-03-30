# Copyright (C) 2007 PreludeIDS Technologies. All Rights Reserved.
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
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.

import siteconfig, gettext, __builtin__


try: 
    import threading    

except ImportError:
    _lock = None
    currentThread = lambda: "none"

else:
    _lock = threading.Lock()
    currentThread = threading.currentThread


_all_locale = { }
_localized_thread = { }    


def _safeGettext(s):
    if _localized_thread.has_key(currentThread()):
        return _localized_thread[currentThread()].gettext(s)
    else:
        return s
    

def setLocale(lang):
    if _lock:
        _lock.acquire()
    
    if not _all_locale.has_key(lang):
        _all_locale[lang] = gettext.translation("prewikka", siteconfig.locale_dir, languages=[lang])
            
    if _lock:
        _lock.release()
            
    _localized_thread[currentThread()] = _all_locale[lang]
   
        
gettext.install("prewikka", siteconfig.locale_dir)
__builtin__._ = _safeGettext
