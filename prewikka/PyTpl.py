"""
PyTpl is a versatile templating engine
"""

import re

class PYTPL_block:
    """
    Main building block of pytpl
    """
    def __init__(self, data):
        """
        """
        self.__B = {}
        self.__output = ""
        self.__isParsed = False
        self.__haveContent = False
        expression = re.compile(
                r"<!--\s+BEGIN\s+([a-zA-Z][a-zA-Z0-9-_]+)"
                r"\s+-->(.*)<!--\s+END\s+\1\s+-->", 
                re.DOTALL)
        self.__content = expression.sub( self.__addToBlockList, data)

    def parse(self, touch=False):
        """
        """
        data = self.__parseVars()
        expression = re.compile(r"{__([a-zA-Z][a-zA-Z0-9_]+)__}", re.DOTALL)
        result = expression.sub(self.__parseBlock, data)

        if self.__haveContent or touch:
            self.__output += result
        self.__isParsed = True

    def __setVar(self, variable, value=""):
        """
        """
        self.__isParsed = False
        setattr(self, variable, value)

    def __get(self):
        """
        """
        if not self.__isParsed: 
            self.parse()
        output = self.__output
        self.__output = ""
        self.__haveContent = False
        return output

    def __str__(self):
        return self.__get()

    def __getitem__(self, blockname):
        """
        """
        return self.__B[blockname]

    def __addToBlockList(self, obj):
        """
        """
        self.__B[obj.group(1)] = PYTPL_block(obj.group(2))
        return "{__%s__}" % (obj.group(1))

    def __parseBlock(self, result):
        """
        """
        output = self.__B[result.group(1)].__get()
        if output != "": 
            self.__haveContent = True
        return output

    def __parseVars(self):
        """
        """
        expression = re.compile(r"{([a-zA-Z][a-zA-Z0-9_]+)}", re.DOTALL)
        output = expression.sub(self.__getVar, self.__content)
        return output

    def __getVar(self, result):
        """
        """
        try:
            data = getattr(self, result.group(1))
            self.__haveContent = True
            return str(data)
        except AttributeError:
            return ""



class PyTpl(PYTPL_block):
    """
    """
    def __init__(self, filename):
        """
        """
        PYTPL_block.__init__(self, file(filename).read())



class Template(PyTpl):
    def __init__(self):
        template_file = self.__module__.replace(".", "/") + ".tpl"
        PyTpl.__init__(self, template_file)
