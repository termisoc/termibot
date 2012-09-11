# -*- coding: utf-8 -*-

import sys
import time
from datetime import datetime
from threading import Thread

import psycopg2

import plugin


class Activity(plugin.Plugin):
    def __init__(self, factory, config):
        self.config = config
        self.activity = {}
        self.messages = {}
        factory.register_filter(r'.*', self.update_activity)
        factory.register_command(u'seen', self.get_last_seen)
        factory.register_command(u'tell', self.add_tell)

        self.conn = psycopg2.connect("dbname=%(dbname)s\
                user=%(user)s host=%(host)s password=%(password)s"
                % config['database'])

        self.run_thread = True
        self.updater = Thread(target=self.update_loop)
        self.updater.daemon = True
        self.updater.start()

    def update_activity(self, user, channel, message):
        user = user[0]
        if user in self.activity:
            del self.activity[user]

        self.activity[user] = {
                'channel': channel,
                'message': message,
                'timestamp': datetime.now(),
                }
        return self.run_tell(user)

    def get_last_seen(self, user, channel, message):
        req_user = message[0]
        if req_user not in self.activity:
            return u'%s has never been seen.' % req_user
        else:
            last_channel = self.activity[req_user]['channel']

            if channel == last_channel:
                last_message = self.activity[req_user]['message']
            else:
                last_message = None

            last_seen = self._timedelta_format(datetime.now() -
                    self.activity[req_user]['timestamp'])

            output = (u'%s was last seen %s ago in %s'
                    % (req_user, last_seen, last_channel))

            if last_message is not None:
                output += u' saying “%s”.' % last_message
            else:
                output += u'.'

        return output

    def add_tell(self, user, channel, message):
        target = message[0]
        if target not in self.messages:
            self.messages[target] = {}
        if user[0] not in self.messages[target]:
            self.messages[target][user[0]] = []

        self.messages[target][user[0]].append(u' '.join(message[1:]))
        return u'Okay, will tell %s on next speaking.' % target

    def run_tell(self, user):
        if not user in self.messages:
            return
        if len(self.messages[user].keys()) == 0:
            return

        output = []
        for sender, messages in self.messages[user].iteritems():
            if len(messages) == 0:
                continue
            for message in messages:
                output.append(u'%s told me to tell you: %s' %
                        (sender, message))
        del self.messages[user]
        return output

    def _timedelta_format(self, delta):
        s = delta.seconds
        days, remainder = divmod(s, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return u'%s days %.2d:%.2d:%.2d' % (days, hours, minutes, seconds)

    def update_loop(self):
        while self.run_thread:
            self.update_db()
            time.sleep(30)

    def update_db(self):
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM last_seen;")
            for user in self.activity.iterkeys():
                value = self.activity[user]
                cur.execute("INSERT INTO last_seen VALUES(%s, %s, %s, %s);",
                    (user, value['channel'], value['message'],
                        value['timestamp']))
            self.conn.commit()

            cur.execute("DELETE FROM user_tells;")
            for target in self.messages.iterkeys():
                for sender, messages in self.messages[user].iteritems():
                    for message in messages:
                        cur.execute(
                                "INSERT INTO user_tells VALUES(%s, %s, %s);",
                                (target, sender, message))
            self.conn.commit()
            print "updated db"
        except Exception as e:
            print >>sys.stderr, e
        finally:
            cur.close()

    def on_reload(self):
        self.run_thread = False

        # one last database update when quitting.
        self.update_db()
