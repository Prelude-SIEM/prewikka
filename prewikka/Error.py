from prewikka import DataSet
from prewikka.templates import ErrorTemplate

class PrewikkaError(Exception):
    pass



class SimpleError(DataSet.BaseDataSet, ErrorTemplate.ErrorTemplate, PrewikkaError):
    def __init__(self, name, message):
        DataSet.BaseDataSet.__init__(self)
        ErrorTemplate.ErrorTemplate.__init__(self)
        self.name = name
        self.message = message
