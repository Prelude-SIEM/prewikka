
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


"""
parses request[variable] = value

"""
import re

class OwnFS:
    """
    parses cgi-parameters
    """
    def __init__(self, fieldstorage):
        """
        does all the dirty work
        """
        self.fieldstorage = fieldstorage
        self.lista = {}
        for key in self.fieldstorage.keys():
            try:
                section, subsection = re.match(\
                        r"([a-zA-Z0-9-_]*)[[]([a-zA-ZZ0-9-_]*)[]]", \
                        key).groups()
                if self.lista.has_key(section):
                    self.lista[section][subsection] = \
                            self.fieldstorage.getvalue(key)
                else:
                    self.lista[section] = {}
                    self.lista[section][subsection] = \
                            self.fieldstorage.getvalue(key)
            except (Exception):
                self.lista[key] = self.fieldstorage.getvalue(key)
            

    def __str__(self):
        """
        just returns parameters as a string
        """
        return str(self.lista)

    def get(self):
        """
        return parameters
        """
        return self.lista
