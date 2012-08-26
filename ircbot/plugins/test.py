# -*- coding: utf-8 -*-

import plugin


class Test(plugin.Plugin):
    def __init__(self, factory, config):
        factory.register_command('hello', self.hello_world)
        factory.register_filter(r'hello', self.hello_world)

    def hello_world(self, user, channel, args):
        if len(args) == 0:
            return u'héllø, wörld'

        return self.get_subcommand('hello_world',
                args[0], user, channel, args[1:])

    def hello_world_english(self, user, channel, args):
        return 'hello, world'

    def hello_world_spanish(self, user, channel, args):
        return u'¡hola, mundo!'
