# -*- coding: utf-8 -*-

import sys
import imp
import re

from twisted.internet import reactor

# dynamic loading throws warnings without this.
import plugins  # NOQA


class PluginFactory(object):
    def __init__(self, config):
        self.config = config

        self.modules = {}
        self.plugins = {}
        self.commands = {}
        self.filters = {}

        for plugin in config['plugins']:
            try:
                print >>sys.stderr, 'trying to load %s' % plugin
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
        self.register_command('version', self.get_version)

    def run(self, user, channel, message):
        if message.startswith('!'):
            # appears to be a command
            words = message.split()
            command = words.pop(0)[1:]

            if command in self.commands:
                return self.commands[command](user, channel, words)
        else:
            # not a command, check if it matches any filters
            output = []
            for pattern, command in self.filters.iteritems():
                if pattern.search(message):
                    result = command(user, channel, message)
                    if isinstance(result, list):
                        output.extend(result)
                    elif result is not None:
                        output.append(result)

            if len(output) > 0:
                return output

    def register_command(self, name, fn):
        self.commands[name] = fn

    def register_filter(self, pattern, fn):
        self.filters[re.compile(pattern)] = fn

    def get_commands(self, *args):
        return u', '.join(self.commands.keys())

    def get_plugins(self, *args):
        return u', '.join(self.plugins.keys())

    def get_filters(self, *args):
        return u', '.join([u'/%s/: %s' % (f.pattern, c.im_class.__name__)
                for f, c in self.filters.iteritems()])

    def get_version(self, *args):
        return u'%s.%s.%s' % self.config['version']

    def reload_plugin(self, user, channel, args):
        plugin = args[0]
        module = imp.load_source('plugins.%s' % plugin,
                'ircbot/plugins/%s.py' % plugin)
        classname = plugin[0].upper() + plugin[1:]

        self.plugins[plugin].on_reload()

        self.modules[plugin] = module
        self.plugins[plugin] = getattr(module, classname)(self, self.config)
