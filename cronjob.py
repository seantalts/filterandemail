#!/usr/home/sean/.virtualenvs/filterandemail/bin/python
import erequests
from itertools import chain
import eventlet
import datetime
import dateutil.parser
import smtplib
import pytz
from email.mime.text import MIMEText

filtr = eventlet.import_patched('filtr')
pile = eventlet.GreenPile()
my_email = 'xitriumcraigslist@gmail.com'
from password import password


def set_last_run(filename="lastrun"):
    with open(filename, "w") as f:
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.timezone("UTC"))
        f.write(now.isoformat())

def get_last_run(filename="lastrun"):
    try:
        with open(filename) as f:
            d = dateutil.parser.parse(f.read())
            return d
    except:
        return ""



def process_feeds(feeds):
    for response, filters in [(erequests.get(url).send(), filters)
                              for url, filters in feeds.iteritems()]:
        pile.spawn(filtr.filter_url, response.text, filters, modified=get_last_run())
    return chain.from_iterable(pile)


def results2msg(results):
    listings = ["\n".join(filter(None, (r['title'], r['description'], r['email'], r['link'])))
                for r in results]
    msg = MIMEText("\n\n".join(listings))
    return msg


def email_results(email_addresses, results):
    server = smtplib.SMTP()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(my_email, password)
    msg = results2msg(results)
    msg['Subject'] = 'craigslist email' if len(results) > 1 else results[0]['title']
    msg['From'] = my_email
    msg['To'] = ", ".join(email_addresses)
    if len(results) == 1:
        msg.add_header('reply-to', results[0]['email'])
    print msg
    server.sendmail(my_email, email_addresses, msg.as_string())
    server.quit()


if __name__ == "__main__":
    from feeds import feeds as FEEDS, email_addresses
    results = list(process_feeds(FEEDS))
    if results:
        email_results(email_addresses, results)
    set_last_run()
