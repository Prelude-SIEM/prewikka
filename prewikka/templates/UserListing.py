from prewikka import PyTpl


class UserListing(PyTpl.Template):
    def __init__(self, listing, add_user_action):
        PyTpl.Template.__init__(self)
        self.LISTING = listing
        self.ACTION = add_user_action
