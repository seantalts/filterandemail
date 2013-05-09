from google.appengine.ext import ndb

class Filter(ndb.Model):
    type = ndb.StringProperty()
    params = ndb.TextProperty()


class RSS(ndb.Model):
    filters = ndb.LocalStructuredProperty(Filter, repeated=True)
    url = ndb.StringProperty()


class Account(ndb.Model):
    owner = ndb.UserProperty()
    id = ndb.StringProperty()
    entries = ndb.LocalStructuredProperty(RSS, repeated=True)
