# -*- coding: utf-8 -*-

from datetime import datetime

import plugin


class Activity(plugin.Plugin):
    def __init__(self, factory, config):
        self.config = config
        self.activity = {}
        self.messages = {}
        factory.register_filter(r'.*', self.update_activity)
        factory.register_command(u'seen', self.get_last_seen)
        factory.register_command(u'tell', self.add_tell)

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

        self.messages[target][user[0]].append(message[1:])
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
                        (sender, u' '.join(message)))
        del self.messages[user]
        return output

    def _timedelta_format(self, delta):
        s = delta.seconds
        days, remainder = divmod(s, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return u'%s days %.2d:%.2d:%.2d' % (days, hours, minutes, seconds)
