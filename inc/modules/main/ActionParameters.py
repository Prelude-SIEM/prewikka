import Interface

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



class Listing(Interface.ActionParameters):
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



class Delete(Listing):
    def register(self):
        Listing.register(self)
        self.registerParameter("idents", list)
        
    def getIdents(self):
        idents = [ ]
        if self.hasParameter("idents"):
            for ident in self["idents"]:
                analyzerid, alert_ident = ident.split(":")
                idents.append((analyzerid, alert_ident))
        
        return idents
