from common import logger, Action

class main(Action):
    def init(self):
        self.name = self.config.get('name', 'noname')

    def run(self, messages):
        print('DEBUG ({0}) {1}'.format(id(self), self.name))
        for message in messages:
            print(message)

