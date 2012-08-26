# -*- coding: utf-8 -*-


class Plugin(object):
    def get_subcommand(self, prefix, subcommand, user, channel, args):
        if prefix + '_' + subcommand not in dir(self):
            return u'Unknown subcommand %s' % subcommand
        else:
            return getattr(self,
                    prefix + '_' + subcommand)(user, channel, args)
