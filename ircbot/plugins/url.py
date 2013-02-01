# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib2

import html5lib
import psycopg2

import plugin


class Url(plugin.Plugin):
    pattern = r'((?:http://|https://|ftp://)[\w\-\@;\/?:&=%\$_.+!*\x27(),~#"]+[\w\-\@;\/?&=%\$_+!*\x27()~"])'  # NOQA
    url_re = re.compile(pattern)
    twit_re = r'https?://([^.]*\.)?twitter.com/.*status(es)?/[0-9]+'

    def __init__(self, factory, config):
        self.config = config
        factory.register_filter(self.pattern, self.scan)
        self.conn = psycopg2.connect("dbname=%(dbname)s\
                user=%(user)s host=%(host)s password=%(password)s"
                % config['database'])

    def scan(self, user, channel, message):
        urls = self.url_re.findall(message)

        output = []
        for url in urls:
            if self.config['plugin_settings']['url']['handle_twitter']:
                if re.match(self.twit_re, url):
                    result = self._handle_twitter(url)
                    if result is not None:
                        output.append(result)
                    continue

            if not self.config['plugin_settings']['url']['print_to_channel']:
                continue

            result = self._handle_url(url, user[0])
            if result is not None:
                output.append(result)

        return output

    def _handle_url(self, url, user):
        short = self._shorten(url)
        title = self._get_title(url)
        first_posted = self._get_first(url, user, short)
        if first_posted is not None:
            return (u'[ %s — %s ] (first posted by %s on %s)' %
                    (short, title, first_posted[0], first_posted[1]))
        else:
            return (u'[ %s — %s ]' % (short, title))

    def _handle_twitter(self, url):
        tweet = re.search(r'/([0-9]+)(/|$)', url).group(1)
        try:
            req = urllib2.urlopen(
                    'http://api.twitter.com/1/statuses/show/%s.json' % tweet)
        except:
            return u'[ unknown ]'

        data = json.loads(req.read())
        if 'retweeted_status' in data and data['retweeted_status']:
            data = data['retweeted_status']
        data['text'] = self._unescape(" ".join(data['text'].split('\n')))
        return '%s (%s): %s (%s)' % (data['user']['name'],
                data['user']['screen_name'], data['text'], data['created_at'])

    def _get_title(self, url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        data = urllib2.urlopen(urllib2.Request(url, headers=headers),
                timeout=5)

        if ';' in data.info()['Content-Type']:
            ctype, encoding = data.info()["Content-Type"].split(";", 2)
            encoding = encoding.split('=')[1]
        else:
            ctype = data.info()['Content-Type']
            encoding = 'utf-8'
        if ctype in ["text/html", "application/xhtml+xml"]:
            xml = html5lib.HTMLParser(
                    tree=html5lib.treebuilders.getTreeBuilder("etree"),
                    namespaceHTMLElements=False).parse(
                            data.read().decode(encoding))
            title = xml.find(".//title")
            if title is not None:
                return re.sub(r"[\n\s]+", " ", title.text.strip())
            else:
                return u"(%s)" % ctype
        else:
            return u"(%s)" % ctype

    def _get_first(self, url, user, short_url):
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM urls WHERE LOWER(url) = LOWER(%s) \
                    OR LOWER(short_url) = LOWER(%s)', (url, url))
            res = cur.fetchone()
        except Exception as e:
            print >>sys.stderr, e
            cur.close()
            return

        if res:
            timestamp = res[1].strftime("%b %d, %Y at %H:%M")
            return (res[3][0] + "\x0f" + res[3][1:], timestamp)
        else:
            try:
                cur.execute(u'INSERT INTO urls VALUES(%s, NOW(), %s, %s)',
                        (url, short_url, user))
                self.conn.commit()
            except Exception as e:
                print >>sys.stderr, e
            finally:
                cur.close()

            return None

    def _shorten(self, url):
        req = urllib2.Request('https://www.googleapis.com/urlshortener/v1/url',
                json.dumps({'longUrl': url}).encode('utf-8'),
                {'Content-Type': 'application/json'})

        try:
            data = urllib2.urlopen(req)
        except:
            return ''

        meta = json.loads(data.read().decode('utf-8'))
        if 'id' in meta:
            return meta['id']
        return ''

    def _unescape(self, text):
        text = re.sub('&amp;', '&', text)
        text = re.sub('&gt;', '>', text)
        text = re.sub('&lt;', '<', text)
        return text
