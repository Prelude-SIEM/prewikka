# Copyright (C) 2004 Nicolas Delon <nicolas@prelude-ids.org>
# All Rights Reserved
#
# This file is part of the Prelude program.
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


from prewikka import Interface

class Message(Interface.ActionParameters):
    def register(self):
        Interface.ActionParameters.register(self)
        self.registerParameter("analyzerid", long)
        self.registerParameter("message_ident", long)

    def setAnalyzerid(self, analyzerid):
        self["analyzerid"] = analyzerid

    def getAnalyzerid(self):
        return self["analyzerid"]

    def setMessageIdent(self, alert_ident):
        self["message_ident"] = alert_ident

    def getMessageIdent(self):
        return self["message_ident"]



class MessageListing(Interface.ActionParameters):
    def register(self):
        self.registerParameter("filter_name", str)
        self.registerParameter("filter_value", str)
        self.registerParameter("timeline_value", int)
        self.registerParameter("timeline_unit", str)
        self.registerParameter("timeline_end", int)
        
    def setFilterName(self, name):
        self["filter_name"] = name

    def getFilterName(self):
        return self.get("filter_name")

    def setFilterValue(self, value):
        self["filter_value"] = value

    def getFilterValue(self):
        return self.get("filter_value")

    def setTimelineValue(self, value):
        self["timeline_value"] = value

    def getTimelineValue(self):
        return self.get("timeline_value")

    def setTimelineUnit(self, unit):
        self["timeline_unit"] = unit

    def getTimelineUnit(self):
        return self.get("timeline_unit")

    def setTimelineEnd(self, end):
        self["timeline_end"] = end

    def getTimelineEnd(self):
        return self.get("timeline_end")



class Delete:
    def register(self):
        self.registerParameter("idents", list)
        
    def getIdents(self):
        idents = [ ]
        if self.hasParameter("idents"):
            for ident in self["idents"]:
                analyzerid, alert_ident = ident.split(":")
                idents.append((analyzerid, alert_ident))
        
        return idents



class MessageListingDelete(MessageListing, Delete):
    def register(self):
        MessageListing.register(self)
        Delete.register(self)
    


class SensorMessageListing(MessageListing):
    def register(self):
        MessageListing.register(self)
        self.registerParameter("analyzerid", long)
        
    def setAnalyzerid(self, analyzerid):
        self["analyzerid"] = analyzerid
        
    def getAnalyzerid(self):
        return self["analyzerid"]



class SensorMessageListingDelete(SensorMessageListing, Delete):
    def register(self):
        SensorMessageListing.register(self)
        Delete.register(self)
