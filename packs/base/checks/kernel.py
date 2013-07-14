from common import logger, Check

import platform

class main(Check):
    def pre_init(self):
        self.default_config = {
            'url': 'https://www.kernel.org/releases.json',
            'moniker': 'stable',
            'show': 1,
            'check_current': False,
        }
        self.validator = {
            'moniker': ['mainline', 'stable', 'longterm', 'linux-next'],
            'show': list(range(1,10)),
            'check_current': bool,
        }

    def init(self):
        self.get_source(
            'releases',
            'flatfile',
            {
                'location': self.config['url'],
                'parser': 'json',
            },
        )
        self.message_defaults.update({
            'kind': 'Kernel',
            'name': self.config['moniker'],
            'weight': 1,
            'location': 'http://www.kernel.org/',
        })
        if self.config['check_current']:
            if platform.system() != 'Linux':
                logger.warning('This is not a Linux system; disabling kernel comparison')
                self.config['check_current'] = False
            else:
                self.current = platform.release().split('_', 1)[0]
                if self.current.count('.') and 'rc' not in self.current:
                    self.current = self.current + '.0'

    def run(self):
        matches = [
            x['version']
            for x in self.sources['releases'].data['releases']
            if x['moniker'] == self.config['moniker']
        ]
        if self.config['check_current']:
            if self.current in matches:
                return []
        return [{'key': x} for x in matches[0:self.config['show']]]

