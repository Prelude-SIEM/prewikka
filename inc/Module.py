import sys
from Query import Query

sys.path.append("inc/modules")

class Module:
    def __init__(self, name, config):
        self.name = name
        self.sections = { }
        self.section_names = [ ]
        self.default_section_name = None
        module = __import__(self.name)
        module.load(self, config)

    def setName(self, name):
        self.name = name

    def getName(self):
        return self.name

    def registerSection(self, name, class_, default=False, parent=None):
        self.sections[name] = { "class": class_, "parent": parent }
        self.section_names.append(name)
        if default:
            self.default_section_name = name

    def build(self, query):
        try:
            section_name = query["section"]
        except KeyError:
            section_name = self.default_section_name

        try:
            section_query = query[section_name]
        except KeyError:
            section_query = query[section_name] = { }

        tmp = self.sections[section_name]
        
        section = self.sections[section_name]["class"](section_query)
        views = { }
        views["layout"] = "normal"
        views["views"] = { }
        views["views"]["main"] = str(section)
        views["views"]["active"] = self.sections[section_name]["parent"] or section_name
        views["views"]["module"] = self.name
        views["views"]["pages"] = filter(lambda name: not self.sections[name]["parent"], self.section_names)
        return views
