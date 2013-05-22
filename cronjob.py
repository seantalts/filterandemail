import erequests
from itertools import chain
import eventlet
from wsgiref.handlers import format_date_time
import time
import datetime
import smtplib
from email.mime.text import MIMEText

filtr = eventlet.import_patched('filtr')
pile = eventlet.GreenPile()
my_email = 'sean@sublevo.com'

def get_now():
    return format_date_time(time.mktime(datetime.datetime.now().timetuple()))


def set_last_run(filename="lastrun"):
    with open(filename, "w") as f:
        f.write(get_now())

def get_last_run(filename="lastrun"):
    try:
        with open(filename) as f:
            return f.read()
    except:
        return ""

def process_feeds(feeds):
    last_run = get_last_run()
    headers = {}
    if last_run:
        headers["If-Modified-Since"] = last_run

    for response, filters in [(erequests.get(url, headers=headers).send(), filters)
                              for url, filters in feeds.iteritems()]:
        pile.spawn(filtr.filter_url, response.text, filters)
    return chain.from_iterable(pile)


def email_results(email_address, results):
    connection = smtplib.SMTP()
    connection.connect()
    listings = ["\n".join((r['title'], r['description'], r['link'])) for r in results]
    print listings
    msg = MIMEText("\n\n".join(listings))
    msg['Subject'] = 'hi'
    msg['From'] = my_email
    msg['To'] = email_address
    connection.sendmail(my_email, [email_address], msg.as_string())


if __name__ == "__main__":
    from feeds import feeds as FEEDS, email_address
    results = process_feeds(FEEDS)
    email_results(email_address, results)
    set_last_run()
