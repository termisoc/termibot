#!/usr/bin/env python
# -*- coding: utf-8 -*-

VERSION = (1, 2, 2)

import sys

from twisted.internet import reactor
from twisted.python import log

import simpleyaml as yaml

import botfactory

log.startLogging(sys.stderr)

if len(sys.argv) > 1:
    config = yaml.load(open(sys.argv[1]))
else:
    log.msg('no config file specified')

config['version'] = VERSION

f = botfactory.BotFactory(config)

# connect factory to this host and port
reactor.connectTCP(config['server'], config['port'], f)

# run bot
reactor.run()
