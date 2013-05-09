from google.appengine.ext import ndb

class Filter(ndb.Model):
    type = ndb.StringProperty()
    fields = ndb.StringProperty(repeated=True)
    params = ndb.TextProperty()


class Feed(ndb.Model):
    filters = ndb.LocalStructuredProperty(Filter, repeated=True)
    url = ndb.StringProperty()


class Account(ndb.Model):
    owner = ndb.UserProperty()
    feeds = ndb.LocalStructuredProperty(Feed, repeated=True)
