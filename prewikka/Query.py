from urllib import urlencode

class Query(dict):
    """
    Query class.

    Responsible for handling input and output queries.
    """
    def __init__(self, field_storage):
        "Initialize the query input part from the field storage of the cgi."
        dict.__init__(self)

        for param in field_storage.keys():
            value = field_storage.getvalue(param)
            #value = field_storage[param]
            l = param.split(".")
            element = l[0]
            if len(l) > 1:
                subelement = l[1]
                if not self.has_key(element):
                    self[element] = { }
                self[element][subelement] = value
            else:
                self[element] = value

    def __str__(self):
        "Convert the query output part into an url encoded string ready to be used in an URL."
        tmp = { }
        for key in self:
            if type(self[key]) is dict:
                for subkey, value in self[key].items():
                    tmp["%s.%s" % (key, subkey)] = value
            else:
                tmp[key] = self[key]
        return urlencode(tmp)


if __name__ == "__main__":
    field_storage = { "toto": "4 2", "foo.bar": "baz" }
    query = Query(field_storage)
    print query["toto"]
##     print query
##     query = Query()
##     query["toto"] = "titi"
##     query["foo"] = { }
##     query["foo"]["bar"] = 42
##     print query
