import sys

import re
import copy
import urllib

class Error(Exception):
    pass


class InvalidFieldError(Error):
    def __init__(self, field):
        self._field = field

    def __str__(self):
        return "invalid field '%s'" % self._field



class InvalidFieldTypeError(Error):
    def __init__(self, field, wanted_type):
        self._field = field
        self._wanted_type = wanted_type

    def __str__(self):
        return "invalid type '%s' for field '%s', '%s' expected" % (type(self._field), self._field, wanted_field)



class AlreadyRegisteredFieldError(Error):
    def __init__(self, field):
        self._field = field

    def __str__(self):
        return "field '%s' is already registered" % self._field



class Request(dict):
    def __init__(self, request=None):
        dict.__init__(self)
        self._fields = { }
        self.register()
        if request:
            for key in self._fields.keys():
                if request.has_key(key):
                    self[key] = request[key]
        
    def register(self):
        pass

    def registerField(self, name, type):
        if self._fields.has_key(name):
            raise AlreadyRegisteredFieldError(name)
        self._fields[name] = type

    def __setitem__(self, name, value):
        field_type = self._fields[name]

        if field_type is list and not type(value) is list:
            value = [ value ]
        
        try:
            value = field_type(value)
        except ValueError:
            raise InvalidFieldTypeError(name, field_type)

        dict.__setitem__(self, name, value)

    def populate(self, fields):
        for name, value in fields.items():
            self[name] = value

    def check(self):
        return True

    def keys(self, ignore=[]):
        return filter(lambda key: not key in ignore, dict.keys(self))
    
    def __copy__(self):
        request = self.__class__()
        request._fields = copy.copy(self._fields)
        for key, value in self.items():
            request[key] = value
         
        return request
     
    def __str__(self):
        return urllib.urlencode(self)
