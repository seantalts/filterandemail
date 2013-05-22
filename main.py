#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import webob.exc as exc
from google.appengine.api import users
from models import Account, ndb, Feed, Filter
import models
import filtr as filter_mod
import os
import datetime

import jinja2

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))


def without_keys(dict_, keys):
    return dict((k, v) for k, v in dict_.iteritems() if k not in set(keys))


class AccountMixin(object):
    def get_account(self):
        user = users.get_current_user()
        if user:
            account = Account.get_by_id(user.user_id())
            if not account:
                self.response.write("MAking account\n")
                account = Account(owner=user, key=ndb.Key(Account, user.user_id()))
                account.put()
            self.account = account
            return account
        else:
            self.redirect(users.create_login_url(self.request.uri))


def feedstr(idx, feed):
    string = ""
    string += "<h2>url: %s</h2><ul>" % feed.url
    for filtr_idx, filtr in enumerate(feed.filters):
        print "hi", filtr
        string += '<li><a href="/feeds/%s/filters/%s">type: %s params: %s</a></li>' % (idx, filtr_idx,
            filtr.type, filtr.params)
    string += "</ul>"
    string += "<h3>Add new filter:</h3>"
    string += """<form action="/feeds/%s" method="post">
                        <input name="params" type="text" value="params">
                        <input type="submit">
                        </form>
                        """ % idx
    return string


def lists(model):
    return dict((key, value) for key, value in model.to_dict().iteritems() if isinstance(value, list))


def modelform(model, forbidden_attrs=set(), basepath=""):
    o = ''
    lists_ = without_keys(lists(model), forbidden_attrs)
    print "hi", model

    for key, value in lists_.iteritems():
        o += "<h1>%s</h1><ul>" % key
        for i, each in enumerate(value):
            o += '<li><a href="%s/%s/%s">%s</a></li>' % (basepath, key, i, each['url'])
        o += "</ul>"
        o += "<h2>Add new %s</h2>" % key
        m = getattr(models, key[:-1].title(), None)
        if m:
            print "hi2", m
            print dir(m)
            print m._properties
            m = m()
            o += modelform(m, lists(m))

    model_dict = without_keys(model._properties, list(forbidden_attrs) + list(lists_))
    if not model_dict:
        return o

    o = '<form action="%s" method="post">' % basepath
    for key, value in model_dict.iteritems():
        if key not in lists_:
            o += '%s: <input type="Text" name=%s value=%s>' % (key, key, value)
    o += '<br><input type="submit"></form>'

    o += '<form action="%s/delete" method="post"><input type="submit" value="delete me">' % basepath

    print "%r" % o
    return o


class MainHandler(webapp2.RequestHandler, AccountMixin):

    def get(self):
        account = self.get_account()
        template = jinja_environment.get_template("index.html")
        self.response.write(template.render({"account": account}))


class DeleteAccount(webapp2.RequestHandler, AccountMixin):
    def post(self):
        account = self.get_account()
        account.key.delete()
        self.redirect("/")


class NewFeedHandler(webapp2.RequestHandler, AccountMixin):
    def post(self):
        """add a new feed to an account"""
        account = self.get_account()
        account.feeds.append(Feed(url=self.request.params['url'],
                                  daily_rate=float(self.request.params['daily_rate'])))
        account.put()
        self.redirect("/feeds/%s" % (len(account.feeds) - 1))


class FeedMixin(AccountMixin):
    def get_feed(self, feed_idx):
        account = self.get_account()
        feed_idx = int(feed_idx)
        if feed_idx > len(account.feeds) - 1:
            raise exc.HTTPNotFound()

        return self.get_account().feeds[feed_idx]

class FeedHandler(webapp2.RequestHandler, FeedMixin):
    def get(self, feed_idx):
        feed = self.get_feed(feed_idx)
        template = jinja_environment.get_template("feed.html")
        template_values = {"feed": feed, "feed_id": feed_idx}
        self.response.write(template.render(template_values))

    def post(self, feed_idx):
        feed = self.get_feed(feed_idx)
        feed.daily_rate = float(self.request.params['daily_rate'])
        feed.url = self.request.params['url']
        self.account.put()
        self.redirect("/feeds/%s" % (feed_idx))


def parse_fields(fields):
    return [f.strip() for f in fields.split(",")]


class NewFilterHandler(webapp2.RequestHandler, FeedMixin):
    def post(self, feed_idx):
        """add a new filter to the feed"""
        feed = self.get_feed(feed_idx)
        feed.filters.append(Filter(type=self.request.params['type'],
                                   params=self.request.params['params'],
                                   fields=parse_fields(self.request.params['fields'])))
        self.account.put()   # eeehh shady
        self.redirect("/feeds/%s" % (len(self.account.feeds) - 1))


class DeleteFeedHandler(webapp2.RequestHandler, AccountMixin):
    def post(self, feed_idx):
        account = self.get_account()
        del account.feeds[int(feed_idx)]
        account.put()
        self.redirect("/")

class FilterHandler(webapp2.RequestHandler, FeedMixin):
    def get(self, feed_idx, filtr_idx):
        feed = self.get_feed(feed_idx)
        filtr = feed.filters[int(filtr_idx)]
        template = jinja_environment.get_template("filter_page.html")
        self.response.write(template.render({"filter": filtr,
                                             "filter_id": filtr_idx,
                                             "feed_id": feed_idx}))

    def post(self, feed_idx, filtr_idx):
        feed = self.get_feed(feed_idx)
        filtr = feed.filters[int(filtr_idx)]
        filtr.type = self.request.params['type']
        filtr.fields = parse_fields(self.request.params['fields'])
        filtr.params = self.request.params['params']
        self.account.put()
        self.redirect(self.request.uri)


class DeleteFilterHandler(webapp2.RequestHandler, FeedMixin):
    def post(self, feed_idx, filter_idx):
        feed = self.get_feed(feed_idx)
        del feed.filters[int(filter_idx)]
        self.account.put()
        self.redirect("/feeds/%s" % feed_idx)


class CronFeedHandler(webapp2.RequestHandler):
    def get(self):
        """email updates"""
        Account.query().map(check_account)
        print 'done'


def check_account(account):
    print 'checking account:', account
    for feed in account.feeds:
        if not feed.last_emailed or (datetime.datetime.now() - feed.last_emailed) > datetime.timedelta(
            hours=(feed.daily_rate or 1) * 24):
            #update feed
            filters = [filter_mod.RegexFilter(filtr.fields, filtr.params) for filtr in feed.filters]
            results = filter_mod.filter_url(feed.url, filters, feed.last_emailed)
            print results
            feed.last_emailed = datetime.datetime.now()
    account.put()


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/delete', DeleteAccount),
    ('/feeds', NewFeedHandler),
    ('/feeds/(\d+)', FeedHandler),
    ('/feeds/(\d+)/delete', DeleteFeedHandler),
    ('/feeds/(\d+)/filters(?:/)?', NewFilterHandler),
    ('/feeds/(\d+)/filters/(\d+)', FilterHandler),
    ('/feeds/(\d+)/filters/(\d+)/delete', DeleteFilterHandler),
    ('/cron/email_feeds', CronFeedHandler),
], debug=True)
