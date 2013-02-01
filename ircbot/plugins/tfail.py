# -*- coding: utf-8 -*-

import urllib

import html5lib

import plugin


class MyUrlOpener(urllib.FancyURLopener):
    version = "Mozilla/4.0"
urllib._urlopener = MyUrlOpener()

line_colours = {
        'Circle': '8,1',
        'Northern': '\x16',
        'Overground': '7',
        'Bakerloo': 5,
        'Central': '4',
        'District': '3',
        'DLR': '10',
        "H'smith & City": '13',
        'Jubilee': '15',
        'Metropolitan': '6',
        'Piccadilly': '2',
        'Victoria': '12',
        'Waterloo and City': '10',
}


class Tfail(plugin.Plugin):
    def __init__(self, factory, config):
        factory.register_command('tfail', self.tfail)

    def tfail(self, user, channel, args):
        url = "http://www.tfl.gov.uk/tfl/livetravelnews/realtime/tube/default.html" # NOQA
        shorturl = "http://goo.gl/A5VjH"
        if len(args) > 0:
            if args[0] == "help":
                return """Usage: !tfail or !tfail tomorrow or !tfail weekend
or !tfail <n>, where <n> is a positive integer number of days in the future to
check. Defaults to today."""
            elif args[0] == 'lines':
                output = []
                for i, j in line_colours.iteritems():
                    output.append(u'\x03%s%s\x0f' % (j, i))
                return u'; '.join(output)

            elif (args[0] == "weekend" or args[0] == "tomorrow" or
                    args[0].isdigit()):
                url = "http://www.tfl.gov.uk/tfl/livetravelnews/realtime/track.aspx?offset=%s" % args[0] # NOQA
                if args[0] == 'weekend':
                    shorturl = 'http://goo.gl/vuol2'

            elif args[0].lower() in [i.lower() for i in line_colours.keys()]:
                data = urllib.urlopen(url, data=urllib.urlencode({})).read()
                xml = html5lib.HTMLParser(
                        tree=html5lib.treebuilders.getTreeBuilder("etree"),
                        namespaceHTMLElements=False).parse(data)
                for line in xml.findall(".//li[@id='%s']" % args[0].lower()):
                    return line[1].text + ". " + shorturl

        data = urllib.urlopen(url, data=urllib.urlencode({})).read()
        xml = html5lib.HTMLParser(
                tree=html5lib.treebuilders.getTreeBuilder("etree"),
                namespaceHTMLElements=False).parse(data)

        lines = {}
        for line in xml.findall(".//li[@class='ltn-line']"):
            if not line[1].text == "Good service":
                lines[line[0].text] = line[1][0].text

        output = []
        for i, j in lines.iteritems():
            if 'severe' in j.lower() or 'suspended' in j.lower():
                j = '\x030,04' + j + '\x03'
            if i in line_colours:
                output.append(u'\x03%s%s\x0f: %s' % (line_colours[i], i, j))
            else:
                output.append(u'\x02%s\x02: %s' % (i, j))
        output = u"; ".join(output)
        if output == "":
            output = "none"
        return (xml.find(".//div[@class='hd-row']/h2").text.strip() + ": "
                + output + ". " + shorturl)
