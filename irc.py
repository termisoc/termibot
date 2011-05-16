#!/usr/bin/env python

import os
import re
import select
import sys

from socket import socket, AF_INET, AF_INET6
from subprocess import Popen, PIPE
from time import sleep

import json
config = json.load(open("subvirc.conf"))
if not 'cmd_char' in config:
    config['cmd_char'] = '!'

def main():
    sock = socket()
    sock.connect((config['server'], 6667))

    sock.sendall("NICK {0}\r\n".format(config['nick']))
    sock.sendall("USER {0} {1} {2} :{3}\r\n".format(config['user'],config['hostname'],config['server'],config['realname']))

    rxsocks = []
    if 'sockets' in config:
        for i in config['sockets']:
            if ":" in i[0]:
                s = socket(AF_INET6)
            else:
                s = socket(AF_INET)
            s.bind((i[0],i[1]))
            s.listen(1)
            rxsocks.append(s)

    pids = []
    try:
        pids.append(os.fork())
        if pids[-1] == 0:
            mainloop(sock) or sys.exit(1)
        for rxsock in rxsocks:
            pids.append(os.fork())
            if pids[-1] == 0:
                listenloop(rxsock, sock) or sys.exit(2)
        os.wait()
    except KeyboardInterrupt:
        sys.exit(0)
    except:
        for pid in pids:
            os.kill(pid, 15)

def mainloop(sock):
    for line in sock.makefile():
        line = line.strip()
        words = line.split()

        print(line)

        if words[1] == "433":
            # nickname already in use.
            config['nick'] += "_"
            sock.sendall("NICK {0}\r\n".format(config['nick']))
        elif words[1] == "376":
            # end of motd.
            for channel in config['channels']:
                sock.sendall("JOIN {0}\r\n".format(channel))
        elif words[0] == "PING":
            sock.sendall("PONG {0}\r\n".format(words[1]))
        elif len(words) > 3 and words[3] == ":" + config['cmd_char'] + "quit":
            sock.sendall("QUIT :Received " + config['cmd_char'] + "quit command.\r\n")
            sys.exit(1)
        elif words[1] == "PRIVMSG":
            if os.fork() == 0:
                handle_privmsg(sock, words)
                sys.exit(0)

def listenloop(rxsock, txsock):
    while True:
        conn, addr = rxsock.accept()
        for line in conn.makefile():
            line = line.strip()
            words = line.split()

            if words[0][0] == '@':
                # message to a person
                txsock.sendall('PRIVMSG {0} :{1}\r\n'.format(words[0][1:], " ".join(words[1:])))
            elif words[0][0] == '#':
                # message to a channel
                txsock.sendall('PRIVMSG {0} :{1}\r\n'.format(words[0], " ".join(words[1:])))
            else:
                print "!!! unrecognised message: " + line

def handle_privmsg(sock, words):
    sender = re.split(r'[:!@]', words[0])
    sender.pop(0)
    to = words[2]

    if words[3][1] == config['cmd_char']:
        cmd = words[3][2:]

        cmd_path = os.path.join(os.dirname(sys.argv[0], "plugins", cmd))
        response = []

        p = Popen([cmd_path], bufsize=1000, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (child_stdin, child_stdout, child_stderr) = (p.stdin, p.stdout, p.stderr)

        for line in p.stderr:
            response.append("ERROR: " + line)
        for line in p.stdout:
            response.append(line)

        if words[2] == config['nick']:
            to = sender[0]
        else:
            response = ["{0}: {1}".format(sender[0], r) for r in response]

        for r in response:
            sock.sendall("PRIVMSG {0} :{1}\r\n".format(to, r))
