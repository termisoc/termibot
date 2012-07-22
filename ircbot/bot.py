# -*- coding: utf-8 -*-

import re

from twisted.words.protocols import irc
from twisted.python import log


class Bot(object, irc.IRCClient):
    def connectionMade(self):
        self.nickname = self.factory.nickname
        irc.IRCClient.connectionMade(self)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        log.msg('Connected.')
        self.join(self.factory.channel)
