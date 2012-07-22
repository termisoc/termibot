# -*- coding: utf-8 -*-


class PluginFactory(object):
    def __init__(self, log):
        self.log = log

    def run(self, user, channel, message):
        return 'hello, world'
