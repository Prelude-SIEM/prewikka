import sys
import os

import Log

class LogStderr(Log.LogBackend):
    def invalidQuery(self, query):
        print >> sys.stderr, "[prewikka] invalid query %s from %s" % (str(query), os.environ["REMOTE_ADDR"])



def load(core, config):
    backend = LogStderr()
    core.log.registerBackend(backend)
