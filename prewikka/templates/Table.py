import sys

from prewikka import PyTpl


class Table(PyTpl.Template):
    def __init__(self):
        PyTpl.Template.__init__(self)
        self._header = None
        self._footer = None
        self._rows = [ ]

    def setHeader(self, header):
        self._header = header

    def setFooter(self, footer):
        self._footer = footer

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

        if self._footer:
            for cell in self._footer:
                self["footer"]["row"]["cell"].CONTENT = cell
                self["footer"]["row"]["cell"].parse()
            self["footer"]["row"].parse()
            self["footer"].parse()

        return PyTpl.Template.__str__(self)
