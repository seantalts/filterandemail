from filtr import RegexFilter
email_address = "xitrium@gmail.com"

feeds = {"http://newyork.craigslist.org/search/aap/que?bedrooms=3&maxAsk=3000&minAsk=1000&query=astoria%20-rego%20-ditmars%20-elmhurst%20-ridgewood%20-kew%20-forest%20-corona%20-woodside%20-jackson%20-flushing&srchType=A&format=rss":
         (
             RegexFilter(['title', 'description'], "3[0-9]"),
             RegexFilter(['title', 'description'], 'broadway'),
         )
         }
