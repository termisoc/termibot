# -*- coding: utf-8 -*-

from twisted.internet import reactor, protocol

import bot


class BotFactory(protocol.ClientFactory):
    """A factory for bots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, config):
        self.config = config
        for key, value in config.iteritems():
            setattr(self, key, value)

    def buildProtocol(self, addr):
        p = bot.Bot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()
