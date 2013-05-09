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
from google.appengine.api import users
from models import Account, ndb, Feed, Filter
import models


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
        self.response.write("""
                            <html><body><p>
                            """)

        self.response.write(modelform(account, ["owner"]))

    def post(self):
        account = self.get_account()
        account.feeds.append(Feed(url=self.request.params['url']))
        account.put()
        self.redirect("")

class DeleteAccount(webapp2.RequestHandler, AccountMixin):
    def post(self):
        account = self.get_account()
        account.key.delete()
        self.redirect("/")


class FeedHandler(webapp2.RequestHandler, AccountMixin):
    def get(self, feed_idx):
        account = self.get_account()
        feed = account.feeds[int(feed_idx)]
        self.response.write(modelform(feed, basepath=self.request.uri))

    def post(self, feed_idx):
        """add a new filter to the feed"""
        account = self.get_account()
        feed = account.feeds[int(feed_idx)]
        feed.filters.append(Filter(type="regex", params=self.request.params['params']))
        account.put()
        self.redirect("/feeds/%s" % len(account.feeds) - 1)

class DeleteFeedHandler(webapp2.RequestHandler, AccountMixin):
    def post(self, feed_idx):
        account = self.get_account()
        del account.feeds[int(feed_idx)]
        account.put()
        self.redirect("/")

class FilterHandler(webapp2.RequestHandler, AccountMixin):
    def get(self, feed_idx, filtr_idx):
        account = self.get_account()
        feed = account.feeds[int(feed_idx)]
        filtr = feed[int(filtr_idx)]


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/delete', DeleteAccount),
    ('/feeds/(\d+)', FeedHandler),
    ('/feeds/(\d+)/delete', DeleteFeedHandler),
    ('/feeds/(\d+)/filters/(\d+)', FilterHandler),
], debug=True)
