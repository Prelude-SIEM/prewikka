import sys

import PyTpl

class Table(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self._header = None
        self._rows = [ ]

    def setHeader(self, header):
        self._header = header

    def addRows(self, rows):
        self._rows += rows

    def addRow(self, row):
        self.addRows([ row ])

    def __str__(self):
        if self._header:
            for cell in self._header:
                self["header"]["row"]["cell"].CONTENT = cell
                self["header"]["row"]["cell"].parse()
            self["header"]["row"].parse()
            self["header"].parse()

        i = 0
        for row in self._rows:
            row_name = ("row_even", "row_odd")[i%2]
            for cell in row:
                self["body"]["row"][row_name]["cell"].CONTENT = cell
                self["body"]["row"][row_name]["cell"].parse()
            self["body"]["row"][row_name].parse()
            self["body"]["row"].parse()
            i += 1
        self["body"].parse()

        return PyTpl.Template.__str__(self)
