import sys
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
    def __init__(self):
        dict.__init__(self)
        self._fields = { }

    def registerField(self, name, type, hidden=False):
        if self._fields.has_key(name):
            raise AlreadyRegisteredFieldError(name)
        self._fields[name] = { "type": type, "hidden": hidden }

    def __setattr__(self, name, value):
        if name == "_fields" or not self._fields.has_key(name):
            dict.__setattr__(self, name, value)
            return

        type = self._fields[name]["type"]

        try:
            value = type(value)
        except ValueError:
            raise InvalidFieldTypeError(name, type)
        
        self[name] = value

    def __getattribute__(self, name):
        if not dict.__getattribute__(self, "_fields").has_key(name):
            return dict.__getattribute__(self, name)
            
        return self[name]

    def populate(self, fields):
        for name, value in fields.items():
            self[name] = value

    def getHiddens(self):
        return filter(lambda name: self._fields[name]["hidden"], self._fields.keys())

    def __str__(self):
        return urllib.urlencode(self)
