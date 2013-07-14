from common import logger

import getpass

try:
    import requests
except ImportError:
    logger.critical('Could not load requests module')

class main(object):
    def __init__(self, config):
        self.config = config

        logger.info('Creating requests session object')
        self.session = requests.Session()
        self.session.verify = self.config.setdefault('verify', True)

        if 'user' in self.config:
            if self.config['user'] == 'AUTO':
                logger.info('Extracting user from system')
                self.config['user'] = getpass.getuser()
            logger.interact('Please enter the password for {0} ({1})'.format(
                self.config['user'],
                self.config['location'],
            ))
            password = getpass.getpass()
            self.session.auth = (self.options['user'], password)

        self.url = self.config['location']

        test = self.session.head(self.url)
        if test.status_code != requests.codes.ok:
            logger.critical('Failed to access {0} ({1})'.format(self.url, test.status_code))

    def run(self):
        request = self.session.get(self.url)
        if request.status_code != requests.codes.ok:
            logger.error('Failed to access {0} ({1})'.format(self.url, request.status_code))
            return False
        return request.text

