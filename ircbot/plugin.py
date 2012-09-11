# -*- coding: utf-8 -*-

import inspect


class Plugin(object):
    def get_subcommand(self, subcommand, user, channel, args):
        parent = inspect.stack()[1][3]
        command = parent + '_' + subcommand
        if command not in dir(self):
            command = parent + '_ALL'
            if command not in dir(self):
                return u'Unknown subcommand %s' % subcommand
            else:
                args.insert(0, subcommand)
        return getattr(self, command)(user, channel, args)

    def on_reload(self):
        pass
