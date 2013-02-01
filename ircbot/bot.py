# -*- coding: utf-8 -*-

import re
import sys

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.words.protocols import irc

import pluginfactory


class Bot(object, irc.IRCClient):
    lineRate = 0.1
    in_channels = []

    def connectionMade(self):
        self.nickname = self.factory.nick
        self.plugins = pluginfactory.PluginFactory(self.factory.config)
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        print >>sys.stderr, 'Connected.'
        if 'nickserv' in self.factory.config:
            self.msg('NickServ', 'identify %s' %
                    self.factory.config['nickserv']['password'])

        join_loop = LoopingCall(self.join_channels)
        join_loop.start(1)

    def joined(self, channel):
        self.in_channels.append(channel)

    def left(self, channel):
        self.in_channels.remove(channel)

    def join_channels(self):
        for channel in self.factory.channels:
            if channel.encode('utf-8') not in self.in_channels:
                self.join(channel.encode('utf-8'))

    def privmsg(self, user, channel, message):
        reactor.callInThread(self.msg_thread, user, channel, message)

    def noticed(self, user, channel, message):
        pass

    def msg_thread(self, user, channel, message):
        user = re.split(r'[!@]', user)
        print >>sys.stderr, 'from %s in %s: "%s"' % (user[0], channel, message)

        try:
            message = message.decode('utf-8')
        except UnicodeDecodeError:
            message = message.decode('iso-8859-15')

        try:
            channel = channel.decode('utf-8')
        except UnicodeDecodeError:
            channel = channel.decode('iso-8859-15')

        reply_to = user[0] if channel == self.nickname else channel
        reply_prefix = user[0] + ': ' if reply_to == channel else ''
        output = self.plugins.run(user, channel, message)

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
        if isinstance(target, unicode):
            target = target.encode('utf-8')
        print >>sys.stderr, 'to %s: "%s"' % (target, message)
        reactor.callFromThread(irc.IRCClient.msg, self, target, message)
