# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib
import urllib2

import html5lib
import psycopg2

import plugin

class MyUrlOpener(urllib.FancyURLopener):
        version = "Mozilla/4.0"
urllib._urlopener=MyUrlOpener()

class Url(plugin.Plugin):
    pattern = r'((?:http://|https://|ftp://)[\w\-\@;\/?:&=%\$_.+!*\x27(),~#"]+[\w\-\@;\/?&=%\$_+!*\x27()~"])'
    url_re = re.compile(pattern)

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
            short = self._shorten(url)
            title = self._get_title(url)
            first_posted = self._get_first(url, user[0])
            if first_posted is not None:
                output.append(u'[%s — %s] (first posted by %s on %s)' %
                        (short, title, first_posted[0], first_posted[1]))
            else:
                output.append(u'[%s — %s]' % (short, title))

        if self.config['plugin_settings']['url']['print_to_channel']:
            return output

    def _get_title(self, url):
        data = urllib.urlopen(url)
        ctype = data.info()["Content-Type"].split(";")[0]
        if ctype in ["text/html", "application/xhtml+xml"]:
            xml = html5lib.HTMLParser(tree=html5lib.treebuilders.getTreeBuilder("etree"), namespaceHTMLElements=False).parse(data.read())
            title = xml.find(".//title")
            if title != None:
                return re.sub(r"[\n\s]+"," ", title.text.strip())
            else:
                return u"(%s)" % ctype
        else:
            return u"(%s)" % ctype

    def _get_first(self, url, user):
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM urls WHERE LOWER(url) = LOWER(%s) OR LOWER(short_url) = LOWER(%s)', (url,url))
            res = cur.fetchone()
        except Exception as e:
            print >>sys.stderr, e
            cur.close()
            return

        if res:
            timestamp = res[1].strftime("%b %d, %Y at %H:%M")
            return (res[3][0]+"\x0f"+res[3][1:], timestamp)
        else:
            try:
                cur.execute(u'INSERT INTO urls VALUES(%s, NOW(), %s, %s)', (url, None, user))
                self.conn.commit()
            except Exception as e:
                print >>sys.stderr, e
            finally:
                cur.close()

            return None

    def _shorten(self, url):
        req = urllib2.Request('https://www.googleapis.com/urlshortener/v1/url', json.dumps({'longUrl': url}).encode('utf-8'), {'Content-Type': 'application/json'})
        try:
            data = urllib2.urlopen(req)
        except:
            return ''

        meta = json.loads(data.read().decode('utf-8'))
        if 'id' in meta:
            return meta['id']
        return ''
