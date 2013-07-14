#!/usr/bin/env python3

from os import chdir
from time import sleep

# Where the magic happens
import common

if __name__ == '__main__':
    # Grab the command line args and calculated verbosity
    (args, verbosity) = common.parse_args()
    # Set up the fancy logger, with optional file logging
    common.configure_logger(verbosity, args.logfile)
    # We're calling this a lot, so let's make it shorter
    logger = common.logger
    # And let's load the config file into common-space
    common.load_configuration(args.configfile)

    # For simplicity, shift to the repo root
    path = common.get_path()
    logger.debug('Changing directory to {0}'.format(path))
    chdir(path)

    # Load checks and actions into the common-space
    # Sources are loaded by the checks themselves
    # Likewise, filters are loaded by actions
    common.get_thing('checks', common.checks)
    common.get_thing('actions', common.actions)

    logger.info('Entering main loop')

    while True:
        messages = []
        now = common.now(update=True)
        logger.info('Looping with timestamp {0}'.format(now))
        for check in common.checks:
            if check.last_check + check.interval < now:
                logger.debug('Running check: {0}'.format(check._name))
                for name, source in check.sources.items():
                    if source.last_check < now:
                        logger.debug('Running source: {0}'.format(name))
                        if source.run():
                            logger.info(
                                'Source was successful: {0}'.format(name)
                            )
                            source.last_check = now
                    else:
                        logger.debug(
                            'Already checked source: {0}'.format(name)
                        )
                check_messages = check.run()
                if check_messages is False:
                    logger.info(
                        'Check was unsuccessful: {0}'.format(check._name)
                    )
                else:
                    logger.info(
                        'Check was successful: {0}'.format(check._name)
                    )
                    check.degraded = False
                    check.last_check = now
                    check.update(check_messages)
            else:
                if not check.degraded:
                    logger.debug(
                        'Trying to degrading {0}'.format(check._name)
                    )
                    if check.degrade():
                        logger.debug(
                            'Check {0} was degraded'.format(check._name)
                        )
                        check.degraded = True
                else:
                    logger.debug(
                        'Skipping {0} for this loop'.format(check._name)
                    )
            logger.debug(
                'Adding {0} messages to stack'.format(len(check.messages))
            )
            messages.extend(check.messages)
        for action in common.actions:
            logger.debug('Running action: {0}'.format(action._name))
            filtered_messages = action.filter(messages)
            logger.debug(
                '{0} messages matched filter'.format(len(filtered_messages))
            )
            action.run(filtered_messages)
        sleep(1)

