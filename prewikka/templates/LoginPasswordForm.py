from prewikka import PyTpl

class LoginPasswordForm(PyTpl.Template):
    def __str__(self):
        self.parse(touch=True)
        return PyTpl.Template.__str__(self)
