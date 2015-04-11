try:
    from threading import local
except ImportError:
    from dummy_threading import local

class Env:
    htdocs_mapping = {}
    threadlocal = local()

env = Env()
