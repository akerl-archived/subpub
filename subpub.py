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
    chdir(path)

    # Load checks and actions into the common-space
    # Sources are loaded by the checks themselves
    # Likewise, filters are loaded by actions
    common.get_thing('checks', common.checks)
    common.get_thing('actions', common.actions)

    while True:
        messages = []
        now = common.now(update=True)
        for check in common.checks:
            if check.last_check + check.interval < now:
                for name, source in check.sources.items():
                    if source.last_check < now:
                        if source.run():
                            source.last_check = now
                check_messages = check.run()
                if check_messages:
                    check.degraded = False
                    check.last_check = now
                    check.update(check_messages)
            else:
                if not check.degraded:
                    if check.degrade():
                        check.degraded = True
            messages.extend(check.messages)
        for action in common.actions:
            filtered_messages = action.filter(messages)
            action.run(filtered_messages)
        sleep(1)

