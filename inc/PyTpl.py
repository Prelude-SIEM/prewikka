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
        self.B = {}
        self._output = ""
        self._isParsed = False
        self._haveContent = False
        expression = re.compile(
                r"<!--\s+BEGIN\s+([a-zA-Z][a-zA-Z0-9-_]+)"
                r"\s+-->(.*)<!--\s+END\s+\1\s+-->", 
                re.DOTALL)
        self._content = expression.sub( self._addToBlockList, data)

    def parse(self, touch=False):
        """
        """
        data = self._parseVars()
        expression = re.compile(r"{__([a-zA-Z][a-zA-Z0-9_]+)__}", re.DOTALL)
        result = expression.sub(self._parseBlock, data)

        if self._haveContent or touch:
            self._output += result
        self._isParsed = True

    def setVar(self, variable, value=""):
        """
        """
        self._isParsed = False
        setattr(self, variable, value)

    def get(self):
        """
        """
        if not self._isParsed: 
            self.parse()
        output = self._output
        self._output = ""
        self._haveContent = False
        return output

    def __getitem__(self, blockname):
        """
        """
        return self.B[blockname]

    def _addToBlockList(self, obj):
        """
        """
        self.B[obj.group(1)] = PYTPL_block(obj.group(2))
        return "{__%s__}" % (obj.group(1))

    def _parseBlock(self, result):
        """
        """
        output = self.B[result.group(1)].get()
        if output != "": 
            self._haveContent = True
        return output

    def _parseVars(self):
        """
        """
        expression = re.compile(r"{([a-zA-Z][a-zA-Z0-9_]+)}", re.DOTALL)
        output = expression.sub(self._getVar, self._content)
        return output

    def _getVar(self, result):
        """
        """
        try:
            data = getattr(self, result.group(1))
            self._haveContent = True
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

