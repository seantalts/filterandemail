import erequests
from itertools import chain
import eventlet
from wsgiref.handlers import format_date_time
import time
import datetime
import dateutil.parser
import smtplib
from email.mime.text import MIMEText

filtr = eventlet.import_patched('filtr')
pile = eventlet.GreenPile()
my_email = 'xitriumcraigslist@gmail.com'
from password import password

def get_now():
    return format_date_time(time.mktime(datetime.datetime.now().timetuple()))


def set_last_run(filename="lastrun"):
    with open(filename, "w") as f:
        f.write(datetime.datetime.now().isoformat())

def get_last_run(filename="lastrun"):
    try:
        with open(filename) as f:
            d = dateutil.parser.parse(f.read())
            print d
            print dir(d)
            return d
    except:
        return ""



def process_feeds(feeds):
    for response, filters in [(erequests.get(url).send(), filters)
                              for url, filters in feeds.iteritems()]:
        pile.spawn(filtr.filter_url, response.text, filters, modified=get_last_run())
    return chain.from_iterable(pile)


def results2msg(results):
    listings = ["\n".join((r['title'], r['description'], r['link'])) for r in results]
    msg = MIMEText("\n\n".join(listings))
    return msg


def email_results(email_address, results):
    server = smtplib.SMTP()
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(my_email, password)
    msg = results2msg(results)
    msg['Subject'] = 'craigslist email %s' % get_now()
    msg['From'] = my_email
    msg['To'] = email_address
    print msg
    server.sendmail(my_email, [email_address], msg.as_string())
    server.quit()


if __name__ == "__main__":
    from feeds import feeds as FEEDS, email_address
    results = process_feeds(FEEDS)
    print results2msg(results)
    #email_results(email_address, results)
    set_last_run()
