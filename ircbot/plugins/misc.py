# -*- coding: utf-8 -*-

import random

import plugin


class Misc(plugin.Plugin):
    def __init__(self, factory, config):
        factory.register_command('flip', self.flip)

    def flip(self, user, channel, args):
        if len(args) == 0:
            return random.choice([u'heads', u'tails'])

        choices = (u' '.join(args)).split(' or ')
        if len(choices) == 1:
            return random.choice([u'yes', u'no'])
        else:
            return random.choice(choices)
