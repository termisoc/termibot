Plugin API
==========

Plugins can be written in any language that the host machine can support. I'm
trying to limit the core set to Python and POSIX shell, just to limit the
number of dependencies, but there are currently also Ruby scripts. (You could
also write them in a compiled language, but don't be such a dick. Unless it's
Haskell.)

Plugins recieve the name of the instance as their first argument, and other data on stdin.

The first line on stdin consists of ``<nick>\t<username>\t<hostname>\t<full irc user/host string>\t<channel>``, where ``channel`` is either the channel in which the command was sent or the user who sent the command via a query.

The second consists of all the arguments given to the command.

Anything sent to stdout will be treated as a response, subject to the following rules:

- if the first word starts with ``#`` it will be assumed to be a channel; the
  entire output line, minus the first word, will be sent to that channel.
- if the first word starts with ``@`` it will assumed to prefix a username; the
  entire output line, minus the first word, will be sent in a query to that
  user.
- otherwise, the entire output line will be sent either in a query to the user
  (if the command was received via a query), or to the channel in which the
  command was received, prefixed with the username of the sender.

Anything sent to stderr will be sent in a query to the user who sent the command.

Command Socket
==============

If configured to listen on a network socket (127.0.0.1/[::1] port 12345, in the
example configuration), you can send text to it  (e.g., the output of
external/asynchronous commands).

Lines are parsed in the same way as described above, under **Plugin API**,
except that lines that do not specify a user or channel will be silently
ignored.
