from prewikka import PyTpl

class LoginPasswordForm(PyTpl.Template):
    def __init__(self, action):
        PyTpl.Template.__init__(self)
        self.ACTION = action
