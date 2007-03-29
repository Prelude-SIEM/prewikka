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
    class dummy:
        pass
                        
    _thread_specific_data = dummy()

else:
    _thread_specific_data = threading.local()



def _safeGettext(s):
    try:
        return _thread_specific_data.translate.gettext(s)
    except AttributeError:
        return s
    
def initLocale(lang):
    _thread_specific_data.translate = gettext.translation("prewikka", siteconfig.locale_dir, languages=[lang])


__builtin__._ = _safeGettext
