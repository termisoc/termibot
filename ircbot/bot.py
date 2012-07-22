# -*- coding: utf-8 -*-

import re

from twisted.words.protocols import irc
from twisted.python import log

import pluginfactory


class Bot(object, irc.IRCClient):
    def connectionMade(self):
        self.nickname = self.factory.nickname
        self.plugins = pluginfactory.PluginFactory(log)
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        log.msg('Connected.')
        self.join(self.factory.channel)

    def privmsg(self, user, channel, message):
        user = re.split(r'[!@]', user)
        log.msg('from %s in %s: "%s"' % (user[0], channel, message))

        reply_to = user[0] if channel == self.nickname else channel
        reply_prefix = user[0] + ': ' if reply_to == channel else ''
        self.msg(reply_to,
                reply_prefix + self.plugins.run(user, channel, message))

    def msg(self, target, message):
        log.msg('to %s: "%s"' % (target, message))
        irc.IRCClient.msg(self, target, message)
