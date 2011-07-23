#!/usr/bin/env python3

import atexit
import json
import os
import re
import select
import signal
import socket
import socketserver
import sys
import threading

from subprocess import Popen, PIPE

config = json.load(open(sys.argv[1]))
if not 'cmd_char' in config:
    config['cmd_char'] = '!'
config['instance'] = config['nick']

def sendall_u(sock, data):
    sock.sendall(bytes(data, "utf-8"))
    print(data.strip())
    sys.stdout.flush()

def mktcphandler(sock):
    class MyTCPHandler(socketserver.StreamRequestHandler):
        def handle(self):
            for line in self.rfile:
                line = str(line, "utf-8")
                line = line.strip()
                words = line.split()

                if len(words) < 1:
                        pass
                elif words[0][0] == '@':
                    # message to a person
                    sendall_u(sock, 'PRIVMSG {0} :{1}\r\n'.format(words[0][1:], " ".join(words[1:])))
                elif words[0][0] == '#':
                    # message to a channel
                    sendall_u(sock, 'PRIVMSG {0} :{1}\r\n'.format(words[0], " ".join(words[1:])))
    return MyTCPHandler

class V6Server(socketserver.TCPServer):
    address_family = socket.AF_INET6

def main():
    addrinfo = socket.getaddrinfo(config['server'], config['port'])
    sock = socket.socket(addrinfo[0][0])
    sock.connect(addrinfo[0][4])

    sendall_u(sock, "NICK {0}\r\n".format(config['nick']))
    sendall_u(sock,"USER {0} {1} {2} :{3}\r\n".format(config['user'],config['hostname'],config['server'],config['realname']))

    rxsocks = []
    if 'sockets' in config:
        for i in config['sockets']:
            addrinfo = socket.getaddrinfo(i[0],i[1])
            if addrinfo[0][0] == 2:
                s = socketserver.TCPServer(addrinfo[0][4], mktcphandler(sock))
            else:
                s = V6Server(addrinfo[0][4], mktcphandler(sock))
            rxsocks.append(s)

    threads = []
    try:
        main_thread = threading.Thread(target=mainloop, args=(sock,), name="mainloop")
        threads.append(main_thread)
        main_thread.daemon = True
        main_thread.start()

        for rxsock in rxsocks:
            threads.append(threading.Thread(target=rxsock.serve_forever, name=rxsock.server_address[0]+":"+str(rxsock.server_address[1])))
            threads[-1].daemon = True
            threads[-1].start()

        while main_thread.is_alive():
            main_thread.join(2**64)
        sys.exit()
    except KeyboardInterrupt:
        sys.exit()

def linesplit(socket):
    # from http://stackoverflow.com/questions/822001/python-sockets-buffering
    buffer = socket.recv(4096) # thx!
    done = False
    while not done:
        if b"\n" in buffer:
            (line, buffer) = buffer.split(b"\n", 1)
            yield line+b"\n"
        else:
            more = socket.recv(4096)
            if not more:
                done = True
            else:
                buffer = buffer+more
    if buffer:
        yield buffer

def mainloop(sock):
    for line in linesplit(sock):
        try:
            line = str(line, 'utf8')
        except UnicodeDecodeError:
            line = str(line,'iso-8859-1')
        line = line.strip()
        words = line.split()

        print(line)
        sys.stdout.flush()

        if words[1] == "433":
            # nickname already in use.
            config['nick'] += "_"
            sendall_u(sock,"NICK {0}\r\n".format(config['nick']))
        elif words[1] == "376":
            # end of motd.
            for channel in config['channels']:
                sendall_u(sock,"JOIN {0}\r\n".format(channel))
        elif words[0] == "PING":
            sendall_u(sock,"PONG {0}\r\n".format(words[1]))
        elif len(words) > 3 and words[3] == ":" + config['cmd_char'] + "quit":
            sendall_u(sock,"QUIT :Received " + config['cmd_char'] + "quit command.\r\n")
            sys.exit()
        elif words[1] == "PRIVMSG":
            privmsg_thread = threading.Thread(target=handle_privmsg, args=(sock,words))
            privmsg_thread.daemon=True
            privmsg_thread.start()

def run_command(sender, channel, cmd, words):
    if re.search(r'[^A-Za-z0-9_]', cmd):
        return ["ERROR: invalid command."]

    sender_parts = re.split(r'[:!@]', sender)

    cmd_path = os.path.join(os.path.dirname(sys.argv[0]), "plugins", cmd)
    if not os.path.exists(cmd_path):
        return []
    p = Popen([cmd_path, config['instance']], bufsize=1000, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    w = lambda s: p.stdin.write(bytes(s, 'utf-8'))
    w("\t".join(sender_parts))
    w("\t" + sender + "\n")
    w(" ".join(words) + "\n")
    p.stdin.close()

    response = []
    for line in p.stderr:
        response.append("ERROR: " + str(line, "utf-8"))
    for line in p.stdout:
        response.append(str(line, "utf-8"))
    return response

def handle_privmsg(sock, words):
    sender = re.split(r'[:!@]', words[0])
    sender.pop(0)
    to = words[2]

    response = []
    if len(words[3]) > 2 and words[3][1] == config['cmd_char']:
        response = run_command(words[0], to, words[3][2:], words[4:])
    else:
        if re.search(r'([+-]{2}|±)(\s|$)', " ".join(words[3:])):
            response += run_command(words[0], to, "karma_filter", [words[3][1:]] + words[4:])
        if re.search(r'https?://', " ".join(words[3:])):
            response += run_command(words[0], to, "url_filter", [words[3][1:]] + words[4:])

    if len(list(filter((lambda x: x.strip() != ""),response))) == 0:
        return
    elif len(response) > 1:
        for r in response:
            sendall_u(sock,"PRIVMSG {0} :{1}\r\n".format(sender[0], r))
    else:
        response = response[0]
        if words[2] == config['nick']:
            to = sender[0]
        else:
            response = "{0}: {1}".format(sender[0], response)
        sendall_u(sock,"PRIVMSG {0} :{1}\r\n".format(to, response))
