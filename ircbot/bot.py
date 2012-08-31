# -*- coding: utf-8 -*-

import re
import sys

from twisted.words.protocols import irc

import pluginfactory


class Bot(object, irc.IRCClient):
    lineRate = 0.1

    def connectionMade(self):
        self.nickname = self.factory.nick
        self.plugins = pluginfactory.PluginFactory(self.factory.config)
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        print >>sys.stderr, 'Connected.'
        print >>sys.stderr, 'Joining: [%s]' % ','.join(self.factory.channels)
        for channel in self.factory.channels:
            self.join(channel)
            print >>sys.stderr, 'Joined %s' % channel

    def privmsg(self, user, channel, message):
        user = re.split(r'[!@]', user)
        print >>sys.stderr, 'from %s in %s: "%s"' % (user[0], channel, message)

        reply_to = user[0] if channel == self.nickname else channel
        reply_prefix = user[0] + ': ' if reply_to == channel else ''
        output = self.plugins.run(user, channel, message.decode('utf-8'))

        if output is None:
            return

        if isinstance(output, str) or isinstance(output, unicode):
            output = [output]

        if len(u' '.join(output)) > 512:
            self.msg(reply_to, reply_prefix +
                    u'Output too long, sending in PM.')
            reply_to = user[0]
            reply_prefix = ''

        for line in output:
            self.msg(reply_to, reply_prefix + line)

    def msg(self, target, message):
        if isinstance(message, unicode):
            message = message.encode('utf-8')
        print >>sys.stderr, 'to %s: "%s"' % (target, message)
        irc.IRCClient.msg(self, target, message)
