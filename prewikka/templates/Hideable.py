from prewikka import PyTpl

class Hideable(PyTpl.Template):
    id = 0
    
    def __init__(self, name, content, hidden=True):
        PyTpl.Template.__init__(self)
        self.DISPLAY = ("block", "none")[hidden]
        self.NAME = name
        self.CONTENT = content
        self.ID = Hideable.id
        Hideable.id += 1
