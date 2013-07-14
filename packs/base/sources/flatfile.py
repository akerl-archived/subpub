from common import logger, Source, library, load_object 
import lib.modlib.modlib as modlib
import lib.conflib.conflib as conflib
import glob


class main(Source):
    required_config = {'location'}
    default_config = {
        'parser': 'raw'
    }

    def init(self):
        library.setdefault(
            'schemas',
            modlib.Modstack(
                formula='packs.{pack}.schemas.{name}',
                target='main',
            )
        )
        library.setdefault(
            'parsers',
            modlib.Modstack(
                formula='packs.{pack}.parsers.{name}',
                target='main',
            )
        )
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

