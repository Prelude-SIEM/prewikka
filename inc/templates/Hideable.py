import PyTpl

class Hideable(PyTpl.Template):
    id = 0
    
    def __init__(self, name, content):
        PyTpl.Template.__init__(self)
        self.NAME = name
        self.CONTENT = content
        self.ID = Hideable.id
        Hideable.id += 1
