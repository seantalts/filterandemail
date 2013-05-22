import erequests
from itertools import chain
import eventlet

filtr = eventlet.import_patched('filtr')
pile = eventlet.GreenPile()



def process_feeds(feeds):
    for response, filters in [(erequests.get(url).send(), filters) for url, filters in feeds.iteritems()]:
        pile.spawn(filtr.filter_url, response.text, filters)
    return chain.from_iterable(pile)


def email_results(email_address, results):
    print email_address, list(r['title'] for r in results)


if __name__ == "__main__":
    from feeds import feeds as FEEDS, email_address
    results = process_feeds(FEEDS)
    email_results(email_address, results)
