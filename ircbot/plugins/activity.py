# -*- coding: utf-8 -*-

from datetime import datetime

import plugin


class Activity(plugin.Plugin):
    def __init__(self, factory, config):
        self.config = config
        self.activity = {}
        factory.register_filter(r'.*', self.update_activity)
        factory.register_command(u'seen', self.get_last_seen)

    def update_activity(self, user, channel, message):
        user = user[0]
        if user in self.activity:
            del self.activity[user]

        self.activity[user] = {
                'channel': channel,
                'message': message,
                'timestamp': datetime.now(),
                }

    def get_last_seen(self, user, channel, message):
        req_user = message[0]
        if req_user not in self.activity:
            return u'%s has never been seen.' % req_user
        else:
            last_message = self.activity[req_user]['message']
            last_channel = self.activity[req_user]['channel']
            last_seen = self._timedelta_format(datetime.now() -
                    self.activity[req_user]['timestamp'])

            return (u'%s was last seen %s ago in %s, saying “%s”.'
                    % (req_user, last_seen, last_channel, last_message))

    def _timedelta_format(self, delta):
        s = delta.seconds
        days, remainder = divmod(s, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return u'%s days %.2d:%.2d:%.2d' % (days, hours, minutes, seconds)
