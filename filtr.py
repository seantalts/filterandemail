import feedparser
from bs4 import BeautifulSoup as Soup
from eventlet.green import urllib2
import eventlet
import re
import unicodedata
from time import mktime
from datetime import datetime
import pytz


def link_url(feed_entry):
    return feed_entry['links'][0]['href']


def fetch(url):
    return Soup(urllib2.urlopen(url))


def normalize(string):
    return " ".join(unicodedata.normalize('NFKD', string).encode('ascii','ignore').lower().split())


parsers = {
    'craigslist.org/': {'title': lambda page: page.find('h2', 'postingtitle').text,
                       'description': lambda page: page.find('section', {'id': 'postingbody'}).text,
                       }
}


def parse_entry(feed_entry):
    for search, functions in parsers.iteritems():
        if search in feed_entry['dc_source']:
            link = link_url(feed_entry)
            page = fetch(link)
            return {'link': link, 'page': page,
                    'title': normalize(functions['title'](page)),
                    'description': normalize(functions['description'](page)),
                    'updated': datetime.fromtimestamp(mktime(feed_entry['updated_parsed'])).replace(
                        tzinfo=pytz.timezone("UTC")),
                    }


def filter_parsed_entries(entries, filters):
    for entry in entries:
        if all(f(entry) for f in filters):
            yield entry


def parsed(entries):
    pile = eventlet.GreenPile()

    for entry in entries:
        pile.spawn(parse_entry, entry)
    return pile


def filter_url(url, filters, modified=None):
    if not url:
        return ()
    feed = feedparser.parse(url)
    filters = list(filters)
    if modified:
        filters.append(lambda f: f['updated'] > modified)
    return filter_parsed_entries(parsed(feed['entries']), filters)


class RegexFilter(object):
    def __init__(self, fields, regex):
        self.fields = fields
        self.regex = regex

    def __call__(self, entry):
        return any(re.search(self.regex, entry[field]) for field in self.fields)

    def __str__(self):
        return "%s(%s, %s)" % (self.__class__, self.fields, self.regex)

class InverseRegexFilter(RegexFilter):
    def __call__(self, entry):
        return not super(InverseRegexFilter, self).__call__(entry)

#ImageFilter!?


if __name__ == "__main__":
    url = 'http://newyork.craigslist.org/search/aap?bedrooms=3&maxAsk=3100&minAsk=1500&query=astoria%20-elmhurst%20-sunnyside%20-woodside%20-jackson%20-flushing%20-garden%20-forest%20-village%20-jamaica%20-ditmars%20&srchType=A&format=rss'
    filters = [RegexFilter(["title"], "subway")]
    for result in filter_url(url, filters):
        print result['title']
