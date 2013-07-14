from common import logger, Filter


class main(Filter):
    def init(self, config):
        if type(config) is dict:
            if {'rule', 'list'}.issubset(config):
                if config['rule'] in ['ANY', 'ALL']:
                    self.rule = config['rule']
                else:
                    logger.critical('Invalid tag rule provided: {0}'.format(config['rule']))
                self.process_tags(config['list'])
            else:
                logger.critical('Invalid option set provided: {0}'.format(config))
        else:
            self.rule = 'ANY'
            self.process_tags(config)

    def process_tags(self, tags):
        if type(tags) is str:
            self.tags = {tags}
        elif type(tags) is list:
            self.tags = set(tags)
        else:
            logger.critical('Unsupport tag format provided: {0}'.format(tags))

    def run(self, message):
        if self.rule == 'ANY' and not self.tags.isdisjoint(message['tags']):
            return True
        elif self.rule == 'ALL' and self.tags.issubset(message['tags']):
            return True
        return False

