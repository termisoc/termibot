# -*- coding: utf-8 -*-

import re
import sys
import time
from datetime import datetime
from threading import Thread

import psycopg2
from dateutil.tz import tzlocal

import plugin


class Activity(plugin.Plugin):
    def __init__(self, factory, config):
        self.config = config
        self.activity = {}
        self.messages = {}
        factory.register_filter(r'.*', self.update_activity_ui)
        factory.register_command(u'seen', self.get_last_seen)
        factory.register_command(u'tell', self.add_tell_ui)

        self.conn = psycopg2.connect("dbname=%(dbname)s\
                user=%(user)s host=%(host)s password=%(password)s"
                % config['database'])

        self.load_from_db()

        self.run_thread = True
        self.updater = Thread(target=self.update_loop)
        self.updater.daemon = True
        self.updater.start()

    def update_activity(self, user, channel, message, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now(tzlocal())
        if user in self.activity:
            del self.activity[user]

        self.activity[user] = {
                'channel': channel,
                'message': message,
                'timestamp': timestamp,
                }

    def update_activity_ui(self, user, channel, message):
        target = self._nick_cleanup(user[0])
        self.update_activity(target, channel, message)
        return self.run_tell(target)

    def get_last_seen(self, user, channel, message):
        req_user = self._nick_cleanup(message[0])
        if req_user not in self.activity:
            return u'%s has never been seen.' % req_user
        else:
            last_channel = self.activity[req_user]['channel']

            if channel == last_channel:
                last_message = self.activity[req_user]['message']
            else:
                last_message = None

            last_seen = self._timedelta_format(datetime.now(tzlocal()) -
                    self.activity[req_user]['timestamp'])

            output = (u'%s was last seen %s ago in %s'
                    % (req_user, last_seen, last_channel))

            if last_message is not None:
                output += u' saying “%s”.' % last_message
            else:
                output += u'.'
            return output

    def add_tell(self, target, sender, message):
        target = self._nick_cleanup(target)
        if target not in self.messages:
            self.messages[target] = {}
        if sender not in self.messages[target]:
            self.messages[target][sender] = []

        self.messages[target][sender].append(message)

    def add_tell_ui(self, user, channel, message):
        self.add_tell(message[0], user[0], u' '.join(message[1:]))
        return u'Okay, will tell %s on next speaking.' % message[0]

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

    def _nick_cleanup(self, nick):
        return re.match(r'.*(?<![^a-z0-9])', nick.lower()).group(0)

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
        except Exception as e:
            print >>sys.stderr, e
        finally:
            cur.close()

        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM user_tells;")
            for target in self.messages.iterkeys():
                for sender, messages in self.messages[user].iteritems():
                    for message in messages:
                        cur.execute(
                                "INSERT INTO user_tells VALUES(%s, %s, %s);",
                                (target, sender, message))
            self.conn.commit()
        except Exception as e:
            print >>sys.stderr, e
        finally:
            cur.close()

    def load_from_db(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * from last_seen;")
            for user, channel, message, timestamp in cur.fetchall():
                self.update_activity(user.decode('utf-8'),
                        channel.decode('utf-8'), message.decode('utf-8'),
                        timestamp)

            cur.execute("SELECT * from user_tells;")
            for target, sender, message in cur.fetchall():
                self.add_tell(target.decode('utf-8'),
                        sender.decode('utf-8'), message.decode('utf-8'))
        except Exception as e:
            print >>sys.stderr, e
        finally:
            cur.close()

    def on_reload(self):
        self.run_thread = False

        # one last database update when quitting.
        self.update_db()
