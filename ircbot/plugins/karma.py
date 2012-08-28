# -*- coding: utf-8 -*-

import psycopg2

import plugin


class Karma(plugin.Plugin):
    def __init__(self, factory, config):
        factory.register_command('karma', self.karma)
        self.conn = psycopg2.connect("dbname=%(dbname)s\
                user=%(user)s host=%(host)s password=%(password)s"
                % config['database'])

    def karma(self, user, channel, args):
        if len(args) == 0:
            return u'No command specified, try !karma help'

        return self.get_subcommand(args[0], user, channel, args[1:])

    def karma_ALL(self, user, channel, args):
        cur = self.conn.cursor()
        cur.execute('SELECT item, SUM(direction) FROM karma WHERE LOWER(item) \
                = LOWER(%s) GROUP BY item', (args[0],))
        item = cur.fetchone()
        return u'karma for “%s” is %s' % item

    def karma_search(self, user, channel, args):
        output = []
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT item,SUM(direction) FROM karma WHERE \
                    LOWER(item) ~ %s GROUP BY item ORDER BY item', (args[0],))
            results = cur.fetchall()
        except:
            pass
        finally:
            cur.close()

        if len(results) == 0:
            return u'no match'

        for item, value in results:
            if item is not None:
                output.append(u'%s: %s' % (item, value))

        return u'; '.join(output)

    # user help.

    def karma_help(self, user, channel, args):
        if len(args) == 0:
            return u'try !karma <item> to get the value of <item>, \
                    or !karma item to match a pattern.'

        return self.get_subcommand(args[0], user, channel, args[1:])

    def karma_help_search(self, user, channel, args):
        return u'!karma search <pattern>: \
                show values of items matching <pattern>.'

    def karma_help_item(self, user, channel, args):
        return u'Recognises double-quoted strings \
                or alpha-numeric strings with underscores.'
