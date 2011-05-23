Plugin API
==========

Plugins can be written in any language that the host machine can support. I'm
trying to limit the core set to Python and POSIX shell, just to limit the
number of dependencies, but there are currently also Ruby scripts. (You could
also write them in a compiled language, but don't be such a dick. Unless it's
Haskell.)

Plugins recieve the name of the instance as their first argument, and other data on stdin.

The first line on stdin consists of ``<nick>\t<username>\t<hostname>\t<full irc user/host string>``.
The second consists of all the arguments given to the command.

Anything you send to stdout will be printed into the channel the plugin was
called from, prefixed with the username (so you don't need to add the username
to the reply yourself). The same goes for stderr, which will additionally be
prefixed with ERROR.

Command Socket
==============

If configured to listen on a network socket (127.0.0.1/[::1] port 12345, in the
example configuration), you can send text to it  (e.g., the output of
external/asynchronous commands).

Lines should start with either the name of a channel to send the message to,
or``@username`` to send to an individual.
