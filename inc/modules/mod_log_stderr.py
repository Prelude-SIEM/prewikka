import sys
import os

import module

class LogStderr(module.LogModule):
    def invalidQuery(self, query):
        print >> sys.stderr, "[prewikka] invalid query %s from %s" % (str(query), os.environ["REMOTE_ADDR"])



def load(core, config):
    module = LogStderr()
    core.log.registerModule(module)
