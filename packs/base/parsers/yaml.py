from common import logger

try:
    import yaml
except ImportError:
    logger.critical('Failed to load PyYAML')


class main(object):
    def __init__(self, config):
        pass

    def run(self, data):
        return yaml.load(data)

