from prewikka import DataSet
from prewikka.templates import ErrorTemplate



class PrewikkaError(Exception):
    pass



class SimpleError(DataSet.BaseDataSet, ErrorTemplate.ErrorTemplate, PrewikkaError):
    def __init__(self, name, message):
        self.dataset = DataSet.DataSet()
        self.dataset["message"] = message
        self.dataset["name"] = name
        self.template_class = ErrorTemplate.ErrorTemplate
