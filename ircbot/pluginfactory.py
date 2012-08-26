# -*- coding: utf-8 -*-

import sys
import imp

from twisted.internet import reactor

# dynamic loading throws warnings without this.
import plugins  # NOQA


class PluginFactory(object):
    def __init__(self, config, log):
        self.log = log
        self.config = config

        self.modules = {}
        self.plugins = {}
        self.commands = {}
        self.filters = {}

        for plugin in config['plugins']:
            try:
                log.msg('trying to load %s' % plugin)
                module = imp.load_source('plugins.%s' % plugin,
                        'ircbot/plugins/%s.py' % plugin)
                classname = plugin[0].upper() + plugin[1:]
                self.modules[plugin] = module
                self.plugins[plugin] = getattr(module, classname)(self, config)

            except Exception as e:
                print >>sys.stderr, e
                reactor.stop()

        self.register_command('plugins', self.get_plugins)
        self.register_command('commands', self.get_commands)
        self.register_command('filters', self.get_filters)
        self.register_command('reload', self.reload_plugin)

    def run(self, user, channel, message):
        if message.startswith('!'):
            # appears to be a command
            words = message.split()
            command = words.pop(0)[1:]

            if command in self.commands:
                return self.commands[command](words)
        else:
            # not a command, check if it matches any filters
            pass

    def register_command(self, name, fn):
        self.commands[name] = fn

    def get_commands(self, args):
        return ', '.join(self.commands.keys())

    def get_plugins(self, args):
        return ', '.join(self.plugins.keys())

    def get_filters(self, args):
        return ', '.join(self.filters.keys())

    def reload_plugin(self, args):
        plugin = args[0]
        module = imp.load_source('plugins.%s' % plugin,
                'ircbot/plugins/%s.py' % plugin)
        classname = plugin[0].upper() + plugin[1:]

        self.modules[plugin] = module
        self.plugins[plugin] = getattr(module, classname)(self, self.config)
