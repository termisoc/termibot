# -*- coding: utf-8 -*-

import re
import sys

import psycopg2

import plugin


class Karma(plugin.Plugin):
    plusminus = ur'([+-]{2}|±)'
    simple_karma = r'[\w-]{2,}'
    quoted_string = r'"(?:(?:\\.)|(?:[^"]))*"'
    karma_word = '(?:^|\s)(' + simple_karma + '|' + quoted_string + ')' + \
            r'(?=(?:\s|$))'
    karma_item = '(?:^|\s)(' + simple_karma + '|' + quoted_string + ')' + \
            plusminus + r'(?=(?:\s|$))'
    karma_item_reason = karma_item + \
            r'(\s+(?:(?:for|because).+?(?=' + karma_item + r'|$)|\([^\)]+\)))?'

    karma_word_re = re.compile(karma_word)
    karma_item_reason_re = re.compile(karma_item_reason)

    def __init__(self, factory, config):
        factory.register_command('karma', self.karma)
        factory.register_filter(self.plusminus, self.scan)
        self.conn = psycopg2.connect("dbname=%(dbname)s\
                user=%(user)s host=%(host)s password=%(password)s"
                % config['database'])

    def scan(self, user, channel, message):
        results = []
        for match in self.karma_item_reason_re.findall(message):
            item, sign, reason = match[0:3]

            if self._cleanup_item(item) == 'me':
                item = user[0]
                if sign != '--':
                    sign = '--'
                    reason = u'for trying to raise their own karma'

            if sign == '++':
                change = 1
                direction = u'up'
            elif sign == '--':
                change = -1
                direction = u'down'
            else:
                change = 0
                direction = u'no change'

            result = u"%s %s (now %%s)" % (item, direction)
            if len(reason.strip()) > 0:
                result += u", with reason"
            else:
                reason = None

            self._set_value(item, change, reason)
            total = self._get_value(item)
            result = result % total

            results.append(result)

        if len(results) == 0:
            return None
        return u"; ".join(results)

    def _set_value(self, item, direction, reason):
        item = self._cleanup_item(item)
        try:
            cur = self.conn.cursor()
            cur.execute("INSERT INTO karma VALUES(%s, NOW(), %s, %s);",
                    (item, direction, reason))
            self.conn.commit()
        except Exception as e:
            print >>sys.stderr, e
        finally:
            cur.close()

    def _get_value(self, item):
        item = self._cleanup_item(item)
        try:
            cur = self.conn.cursor()
            cur.execute('SELECT SUM(direction) FROM karma WHERE \
                    LOWER(item) = LOWER(%s)', (item,))
            result = cur.fetchone()[0]
            if result is None:
                result = 0
        except Exception as e:
            print >>sys.stderr, e
            result = 0
        finally:
            cur.close()
            return result

    def _cleanup_item(self, item):
        if item.startswith(u'"'):
            item = item[1:-1]
        else:
            item = re.sub('_', ' ', item)
        return item

    def karma(self, user, channel, args):
        if len(args) == 0:
            return u'No command specified, try !karma help'

        return self.get_subcommand(args[0], user, channel, args[1:])

    def karma_ALL(self, user, channel, args):
        items = self.karma_word_re.findall(u' '.join(args))
        output = [u'karma for “%s” is %s' %
                (item, self._get_value(item)) for item in items]
        return u'; '.join(output)

    def karma_search(self, user, channel, args):
        output = []
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT LOWER(item),SUM(direction) FROM karma \
                    WHERE LOWER(item) ~ %s \
                    GROUP BY LOWER(item) ORDER BY LOWER(item)', (args[0],))
            results = cur.fetchall()
        except Exception as e:
            print >>sys.stderr, e
            cur.close()
            return

        if len(results) == 0:
            return u'no match'

        for item, value in results:
            if item is not None:
                output.append(u'“%s”: %s' % (item.decode('utf-8'), value))

        return u'; '.join(output)

    # user help.

    def karma_help(self, user, channel, args):
        if len(args) == 0:
            return u'try !karma <item> to get the value of <item>, \
                    or !karma search <pattern> to match a pattern.'

        return self.get_subcommand(args[0], user, channel, args[1:])

    def karma_help_search(self, user, channel, args):
        return u'!karma search <pattern>: \
                show values of items matching <pattern>.'

    def karma_help_item(self, user, channel, args):
        return u'Recognises double-quoted strings \
                or alpha-numeric strings with underscores.'
