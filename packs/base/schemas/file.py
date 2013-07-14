from common import logger

import os

class main(object):
    def __init__(self, config):
        self.location = os.path.expanduser(config['clean_location'])

    def run(self):
        with open(self.location) as handle:
            return handle.read()

