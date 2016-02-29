from prewikka import error
from prewikka.dataprovider import DataProviderNormalizer

class DataProviderNormalizerGeneric(DataProviderNormalizer):
    def __init__(self, time_field=None):
        if time_field is None:
            raise error.PrewikkaUserError(_("Backend normalization error"),
                                              _("Backend normalization error"))

        self._time_field = time_field

    def parse_paths(self, paths):
        return paths

    def parse_criteria(self, criteria, type):
        parsed_criteria = []

        for criterion in criteria:
            try:
                parsed_criteria.append(criterion % { 'backend' : type, 'time_field' : self._time_field })
            except:
                parsed_criteria.append(criterion)

        return parsed_criteria
