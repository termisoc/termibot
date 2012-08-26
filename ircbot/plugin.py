# -*- coding: utf-8 -*-

import inspect


class Plugin(object):
    def get_subcommand(self, subcommand, user, channel, args):
        parent = inspect.stack()[1][3]
        if parent + '_' + subcommand not in dir(self):
            return u'Unknown subcommand %s' % subcommand
        else:
            return getattr(self,
                    parent + '_' + subcommand)(user, channel, args)
