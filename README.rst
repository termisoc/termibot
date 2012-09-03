Running
=======

Create a Postgres database. Run ``termibot.sql`` to create the tables.

Install the Python requirements using pip.

Then::

    python ./ircbot ./example.conf

Plugin development
==================

Take a look at ircbot/plugins/test.py for an example.

Submitting patches
==================

I use ``git flow`` to manage branches and ``flake8`` to check code before
committing. I suggest you do the same.
