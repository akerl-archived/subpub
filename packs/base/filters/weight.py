from common import logger, Filter

class main(Filter):
    def init(self, config):
        # If this is an integer, make it a length 1 list
        if type(config) is int:
            self.weights = [config]
        # If this is a list, use it as is
        elif type(config) is list:
            # Make sure all the items are integers first
            if not all([type(x) is int for x in config]):
                logger.critical(
                    'Malformed weight list provided: {0}'.format(config)
                )
            else:
                self.weights = config
        # If it's a dict, make a range from the key to the value
        elif type(config) is dict and len(config) == 1:
            (lower, upper) = config.popitem()
            # Add 1 to account for Python's range bounding
            self.weights = range(lower, upper+1)
        else:
            logger.critical(
                'Malformed weight options provided: {0}'.format(config)
            )
        logger.debug('Using weight list: {0}'.format(self.weights))

    def run(self, message):
        if message['weight'] in self.weights:
            return True
        return False

