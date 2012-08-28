# -*- coding: utf-8 -*-

import inspect


class Plugin(object):
    def get_subcommand(self, subcommand, user, channel, args):
        parent = inspect.stack()[1][3]
        command = parent + '_' + subcommand
        if command not in dir(self):
            if parent + '_ALL' not in dir(self):
                return u'Unknown subcommand %s' % subcommand
            else:
                command = parent + '_ALL'
                args.insert(0, subcommand)
        return getattr(self, command)(user, channel, args)
