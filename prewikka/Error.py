from prewikka import DataSet
from prewikka.templates import ErrorTemplate

class BaseError(Exception):
    pass



class SimpleError(DataSet.BaseDataSet, ErrorTemplate.ErrorTemplate, BaseError):
    def __init__(self, name, message):
        DataSet.BaseDataSet.__init__(self)
        ErrorTemplate.ErrorTemplate.__init__(self)
        self.name = name
        self.message = message
