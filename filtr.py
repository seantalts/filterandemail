import feedparser
from bs4 import BeautifulSoup as Soup
import urllib2
import re


def link_url(feed_entry):
    return feed_entry['links'][0]['href']


def fetch(url):
    return Soup(urllib2.urlopen(url))


parsers = {
    'craigslist.org/': {'title': lambda page: page.find('h2', 'postingtitle').text.strip().lower(),
                       'description': lambda page: " ".join(page.find('section', {'id': 'postingbody'}).text.split()).lower(),
                       }
}


def parse_entry(feed_entry):
    for search, functions in parsers.iteritems():
        if search in feed_entry['dc_source']:
            link = link_url(feed_entry)
            page = fetch(link)
            return {'link': link, 'page': page,
                    'title': functions['title'](page),
                    'description': functions['description'](page),
                    }


def filter_parsed_entries(entries, filters):
    for entry in entries:
        if all(f(entry) for f in filters):
            yield entry


def parsed(entries):
    return (parse_entry(entry) for entry in entries)


def filter_url(url, filters):
    feed = feedparser.parse(url)
    print feed['updated']
    return filter_parsed_entries(parsed(feed['entries']), filters)


class RegexFilter(object):
    def __init__(self, fields, regex):
        self.fields = fields
        self.regex = regex


    def __call__(self, entry):
        return any(re.search(self.regex, entry[field]) for field in self.fields)


#ImageFilter!?


if __name__ == "__main__":
    url = 'http://newyork.craigslist.org/search/aap?bedrooms=3&maxAsk=3100&minAsk=1500&query=astoria%20-elmhurst%20-sunnyside%20-woodside%20-jackson%20-flushing%20-garden%20-forest%20-village%20-jamaica%20-ditmars%20&srchType=A&format=rss'
    filters = [RegexFilter(["title"], "subway")]
    for result in filter_url(url, filters):
        print result['title']
