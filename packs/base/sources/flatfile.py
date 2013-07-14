from common import logger, Source, load_object
import lib.modlib.modlib as modlib
import lib.conflib.conflib as conflib
import glob


class main(Source):
    def pre_init(self):
        self.required_config = {'location'}
        self.default_config = {
            'parser': 'raw'
        }

    def init(self):
        if '://' not in self.config['location']:
            schema = 'file'
        else:
            (schema, location) = self.config['location'].split('://', 1)
        config = conflib.Config(
            self.config,
            {
                'schema': schema,
                'clean_location': location,
            }
        ).options
        self.getter = load_object('schemas', schema)(config)
        self.parser = load_object('parsers', self.config['parser'])(config)

    def run(self):
        data = self.getter.run()
        if data is False:
            return False
        data = self.parser.run(data)
        if data is False:
            return False
        self.data = data
        return True

