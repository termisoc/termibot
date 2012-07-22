#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from twisted.internet import reactor
from twisted.python import log

import botfactory


log.startLogging(sys.stderr)
f = botfactory.BotFactory(sys.argv[1], sys.argv[2])

# connect factory to this host and port
reactor.connectTCP("irc.oftc.net", 6667, f)

# run bot
reactor.run()
