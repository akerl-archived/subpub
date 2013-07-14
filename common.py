# Common state module and helper functions

# imports make the world go 'round
import argparse
import logging
import yaml
import os
import datetime
import signal
import lib.modlib.modlib as modlib
import lib.conflib.conflib as conflib

# Meta info lives here
VERSION = '0.0.1'
AUTHOR = 'akerl'
EMAIL = 'me@lesaker.org'
URL = 'https://github.com/akerl/subpub.git'


def parse_args():
    parser = argparse.ArgumentParser(
        description='Input/output manager'  # Least descriptive name ever
    )
    parser.add_argument(
        '--version',
        action='version',
        version=VERSION,
    )
    parser.add_argument(
        '-c', '--config',
        help='config file to use',
        metavar='FILE',
        default='~/.subpub',
        dest='configfile',
    )
    parser.add_argument(
        '-l', '--log',  # Defaults to "don't log to a file"
        help='file to log to',
        metavar='FILE',
        dest='logfile',
    )
    parser.add_argument(
        '-v', '--verbose',
        help='increase verbosity',
        action='count',
        default=0,
    )
    parser.add_argument(
        '-q', '--quiet',
        help='decrease verbosity',
        action='count',
        default=0,
    )
    args = parser.parse_args()
    # This fancy formula normalizes verbosity against the scale use by logging
    verbosity = min(max(30 - 10 * (args.verbose - args.quiet), 0), 60)
    # The logger doesn't exist yet, so we've got to do this the unfancy way
    if verbosity <= 10:  # 10 and under is logger-level for "debug"
        print('Command line arguments: {0}'.format(args))
        print('Calculated verbosity score: {0}'.format(verbosity))
    return (args, verbosity)


def configure_logger(verbosity, logfile):
    # This is the fancy string used for logging stuff
    format_string = '{asctime} {module} {levelname} - {message}'
    # Adding the "INTERACT" level, scored 60 so it always shows up on screen
    # This is used for modules that want to log while interacting with the user
    logging.addLevelName(60, 'INTERACT')
    # Set the default level to 0, so that verbosity works on handlers
    logger.setLevel(0)

    # This is the handler for stdout
    terminal_handler = logging.StreamHandler()
    terminal_handler.setLevel(verbosity)
    terminal_formatter = logging.Formatter(
        fmt=format_string,
        style='{',  # "{" means "use .format() style"
        datefmt='%X',  # Just the HH:MM:SS
    )
    terminal_handler.setFormatter(terminal_formatter)
    logger.addHandler(terminal_handler)
    logger.debug('Terminal logging configured')
    logger.info('Verbosity set at {0}'.format(verbosity))

    if logfile is None:
        return

    # Send it to a file
    file_handler = logging.FileHandler(os.path.expanduser(logfile))
    file_handler.setLevel(0)  # Everything
    file_formatter = logging.Formatter(
        fmt=format_string,
        style='{',  # Again, .format() style
        datefmt='%Y-%m-%d %X',  # YYYY-MM-DD HH-MM-SS
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.debug('Logging to file: {0}'.format(logfile))


def load_configuration(config_file):
    config_file = os.path.expanduser(config_file)
    if not os.path.isfile(config_file):
        logger.critical(
            'Configuration file not found: {0}'.format(config_file)
        )
    logger.info('Using configuration file: {0}'.format(config_file))
    with open(config_file) as handle:
        tmp_config = yaml.load(handle.read())

    required_attributes = frozenset({'checks', 'actions'})
    missing = required_attributes.difference(tmp_config.keys())
    if len(missing):
        logger.critical('Missing required attribute(s): {0}'.format(missing))
    config.update(tmp_config)
    logger.info('Configuration successfully loaded')


# Recursion is fun
def follow_symlink(path):
    if os.path.islink(path):
        return follow_symlink(os.readlink(path))
    return path


# This gets the real location, even behind symlinks
def get_path():
    first_location = os.path.abspath(__file__)
    real_location = follow_symlink(first_location)
    return os.path.dirname(real_location)


# Catches keyboard interrupts (ctrl-c) and dies cleanly
def catch_interrupt(signal, frame):
    print()
    logger.critical('Caught interrupt, dying')


# Maintain now timestamp for start of current run
def now(update=False):
    global now_stamp
    if update is True:
        now_stamp = datetime.datetime.now()
    return now_stamp


# Fancy modlib-based module loader
def load_object(kind, raw_name):
    # If no pack is given, default to 'base'
    if '.' not in raw_name:
        raw_name = 'base.' + raw_name
    (pack, name) = raw_name.split('.')
    logger.info('Loading {0} from {1}'.format(raw_name, kind))
    return library[kind].get(pack=pack, name=name)


def get_source(name, config):
    for source in sources:
        if source._name == name and source.config == config:
            # if there's an existing identical source, return it
            logger.debug('Found existing source for {0}'.format(name))
            return source
    # else, load the source in
    new_source = load_object('sources', name)(config)
    # inject its name for later matching and add it to the list
    new_source._name = name
    sources.append(new_source)
    return new_source


def get_thing(kind, container):
    global_config = config['options']
    for item in config[kind]:
        local_config = item.get('options', dict())
        # Stack a config of global<-local
        this_config = conflib.Config(global_config, local_config).options
        # Get a new object of this type and instantiate with the config
        new_object = load_object(kind, item['type'])(this_config)
        # Inject the name for later use
        new_object._name = item['type']
        container.append(new_object)
    if not len(container):
        # We didn't load anything of this type
        logger.critical('No {0} loaded'.format(kind))


# Extension of logging class
class MyLogger(logging.getLoggerClass()):
    # We want to exit on critical issues
    def critical(self, *args, **kwargs):
        super().critical(*args, **kwargs)
        raise SystemExit

    # This is used to ensure dialog reaches the user and logs
    def interact(self, *args, **kwargs):
        self.log(60, *args, **kwargs)


# Overall class, holds default attributes
class Subpub(object):
    def __init__(self, config):
        self.required_config = set()
        self.default_config = dict()
        self.validator = dict()

        self.pre_init()
        self.init_config(config)
        self.validate_config()
        self.init()

    def pre_init(self):
        pass

    def init_config(self, config):
        self.config = conflib.Config(self.default_config, config).options
        # Grab any keys in required_config that aren't in self.config
        missing = self.required_config.difference(self.config.keys())
        if len(missing):
            logger.critical(
                'Missing required config attributes: {0}'.format(missing)
            )

    def validate_config(self):
        # Exists so that modules can override to validate user settings
        pass

    def init(self):
        # Should be overridden to set up anything the module needs
        pass


class Source(Subpub):
    # fromordinal(1) is used to get a date that's definitely far in the past
    # this ensures all checks run the first time the main loop runs
    last_check = datetime.datetime.fromordinal(1)
    data = None

    def run(self):
        # Where the action happens during the main processing loop
        # This needs to return True/False for success/failure
        return True


class Check(Subpub):
    # fromordinal(1) is used to get a date that's definitely far in the past
    # this ensures all checks run the first time the main loop runs
    last_check = datetime.datetime.fromordinal(1)
    # These calcs are either None or lambda functions to adjust weights
    weight_calc = None
    degrade_calc = None
    degraded = False

    def __init__(self, config):
        # sources dict should be populated with "name: Source" items
        # for sanity, use self.get_source(unique_name, name, config)
        self.sources = {}
        self.messages = []

        # Default message parts
        self.message_defaults = {
            'tags': set(),
            'attributes': {},
        }

        super().__init__(config)


        # Turn the interval into a fancy timedelta
        self.interval = datetime.timedelta(seconds=self.config['interval'])

        # Parse the provided tag(s) into the message_defaults
        tags = self.config.get('tags')
        if type(tags) is str:
            self.message_defaults['tags'].add(tags)
        elif type(tags) is list:
            self.message_defaults['tags'].update(tags)
        elif tags is not None:
            logger.critical('Invalid tag data provided: {0}'.format(tags))

        # Parse the provided weight calc
        weight_calc = self.config.get('weight_calc')
        if type(weight_calc) is int:
            self.weight_calc = lambda x: x + weight_calc
        elif type(weight_calc) is str and weight_calc[0] == '/':
            self.weight_calc = lambda x: x / weight_calc
        elif weight_calc is not None:
            logger.critical(
                'Bad weight_calc provided: {0}'.format(weight_calc)
            )

        # Parse the provided degrade calc
        degrade_calc = self.config.get('degrade_calc')
        if type(degrade_calc) is int:
            self.degrade_calc = lambda x: x + degrade_calc
        elif type(degrade_calc) is str and degrade_calc[0] == '/':
            self.degrade_calc = lambda x: x / degrade_calc
        elif degrade_calc is not None:
            logger.critical(
                'Bad degrade_calc provided: {0}'.format(degrade_calc)
            )

        logger.debug('Message defaults: {0}'.format(self.message_defaults))

    def run(self):
        # Where the action happens during the main processing loop
        # Should return False for failure, list of messages for success
        return []

    # Updates the message queue, adds 'new' tag to new stuff
    def update(self, messages):
        new_messages = []
        for message in messages:
            compiled_message = self.build_message(**message)
            if compiled_message not in self.messages:
                compiled_message['tags'].add('new')
            new_messages.append(compiled_message)
        self.messages = new_messages
                

    # fancy helper to check message_parts and message_defaults
    def build_message(self, **kwargs):
        message = conflib.Config(self.message_defaults, kwargs).options
        # Check for missing parts
        missing = message_parts.difference(message)
        if len(missing):
            logger.critical(
                'Message missing required parts: {0}'.format(missing)
            )
            logger.debug('Message: {0}'.format(message))
        # Apply a weight_calc, if it exists
        if self.weight_calc is not None:
            message['weight'] = self.weight_calc(message['weight'])
        logger.debug('Adding message: {0}'.format(message))
        return message

    def degrade(self):
        new_messages = []
        for message in self.messages:
            # Remove the "new" tag
            message['tags'].discard('new')
            # Perform the degradation calc on the message weight
            if self.degrade_calc is not None:
                message['weight'] = self.degrade_calc(message['weight'])
            # If the weight isn't sub-zero, keep the message
            if message['weight'] > 0:
                new_messages.append(message)
        self.messages = new_messages
        # Returning true for success is super important!
        # True/False return value detemines if degrade() runs on the next loop
        return True

    # Helper method to get a source and add it to this check object
    def get_source(self, unique_name, name, config):
        self.sources[unique_name] = get_source(name, config)


class Action(Subpub):
    def __init__(self, config):
        self.filters = []
        super().__init__(config)

        filters = self.config.get('for')
        # If filters is a dict, it's really just a single filter item
        # Put it as the only item in a list so it parses like the rest
        if type(filters) is dict:
            filters = [filters]
        if type(filters) is list:
            # Create a list of lists of filters.
            # A message matches if any full list of filter rules in
            # self.filters is true
            for this_filter in filters:
                filter_rules = []
                for name, options in this_filter.items():
                    filter_object = load_object('filters', name)
                    filter_rules.append(filter_object(options))
                self.filters.append(filter_rules)
        else:
            logger.critical('Malformed filters provided')

    def filter(self, messages):
        # If there are no filters, all messages pass
        if not len(self.filters):
            return messages
        filtered_messages = []
        for message in messages:
            for this_filter_set in self.filters:
                # Do all filters in this filter_set match
                if all([x.run(message) for x in this_filter_set]):
                    # If so, this message passes; skip to the next message
                    filtered_messages.append(message)
                    break
        return filtered_messages

    # Does the needful
    def run(self, messages):
        pass


class Filter(object):
    def __init__(self, config):
        self.init(config)

    # Made to be overridden by the module writer
    def init(self, config):
        pass

    # Run to filter messages, True = matches, False = doesn't match
    def run(self, message):
        return True

# Instantiate the extended logger object
logging.setLoggerClass(MyLogger)
logger = logging.getLoggerClass()('subpub')

# Add the signal so that ctrl-c is caught cleanly
signal.signal(signal.SIGINT, catch_interrupt)

# Synchronizing timestamp
now_stamp = now(update=True)

# Basic default config
config = {
    'options': {
        'interval': 10,
    }
}

# These are the sources/checks/actions actively in use
sources = []
checks = []
actions = []

# This is the dynamic module library
library = {
    'sources': modlib.Modstack(
        formula='packs.{pack}.sources.{name}',
        target='main',
    ),
    'checks': modlib.Modstack(
        formula='packs.{pack}.checks.{name}',
        target='main',
    ),
    'actions': modlib.Modstack(
        formula='packs.{pack}.actions.{name}',
        target='main',
    ),
    'filters': modlib.Modstack(
        formula='packs.{pack}.filters.{name}',
        target='main',
    ),
}

message_parts = frozenset({
    'name',  # Pretty straightforward. Should be short/concise/etc
    'kind',  # More generic type name
    'key',  # Unique identifier. Uniqueness not totally guaranteed
    'location',  # URL/path/etc
    'weight',  # An integer used mostly for filtering
    'tags',  # A set used mostly for filtering. "new" is a reserved keyword
    'attributes',  # Any extra attributes, can be used to enhance actions
})

