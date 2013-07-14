from common import logger, Source

import os


class main(Source):
    def pre_init(self):
        self.required_config = {'location'}

    def init(self):
        self.location = os.path.expanduser(self.config['location'])
        if not os.path.isfile(self.location):
            logger.critical(
                'Followfile does not exist: {0}'.format(self.location)
            )
        self.handle = open(self.location)
        self.handle.seek(0, 2)

    def run(self):
        new_lines = []
        while True:
            start_of_line = self.handle.tell()
            line = self.handle.readline()
            if not line:
                self.handle.seek(start_of_line)
                break
            new_lines.append(line.rstrip())
        return new_lines

