## class Module:
##     def __init__(self, name, section_name, query):
##         self.__query = query
##         self.__section_name = section_name
##         self.__module = __import__("mod_%s" % name)
##         self.__main = getattr(self.__module, "Main")
##         if section_name:
##             self.__section = getattr(self.__module, "Section%s" % section_name)
##         else:
##             self.__section = self.__main.default_section

##     def build(self):
##         main = self.__main(self.__query)
##         section = self.__section(self.__query)
##         views = main.build(section)
##         views["views"]["active"] = self.__section_name
##         views["views"]["pages"] = [ ]
##         syms = { }
##         for sym_name in dir(self.__module):
##             if re.compile("^Section").match(sym_name):
##                 sym = getattr(self.__module, sym_name)
##                 if hasattr(sym, "name"):
##                     syms[sym_name] = sym

##         names = syms.keys()
##         names.sort(lambda x, y: syms[y].index - syms[x].index)
                
##         for name in names:
##             tmp = (re.sub("^Section", "", name), syms[name].name)
##             sys.stderr.write("%s %s\n" % tmp)
##             views["views"]["pages"].append(tmp)
            
##         return views

import sys
from Query import Query

sys.path.append("inc/modules")

class Module:
    def __init__(self, mod_name):
        self.name = mod_name[4:]
        self.sections = { }
        self.section_names = [ ]
        self.default_section_name = None
        module = __import__(mod_name)
        module.load(self)

    def setName(self, name):
        self.name = name

    def registerSection(self, name, class_, default=False, visible=True):
        self.sections[name] = { "class": class_, "visible": visible }
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

        sys.stderr.write("section query: %s\n" % str(section_query))

        tmp = self.sections[section_name]
        
        section = self.sections[section_name]["class"](section_query)
        section_content = str(section)
        views = { }
        views["layout"] = "normal"
        views["views"] = { }
        views["views"]["main"] = section
        views["views"]["active"] = section_name
        sys.stderr.write(section_name + "\n")
        views["views"]["pages"] = filter(lambda name: self.sections[name]["visible"], self.section_names)
        return views
