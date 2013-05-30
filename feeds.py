from filtr import RegexFilter, InverseRegexFilter
email_addresses = ["xitrium@gmail.com", "adared@gmail.com"]

feeds = {"http://newyork.craigslist.org/search/aap/que?bedrooms=3&maxAsk=3000&minAsk=1000&query=astoria%20-rego%20-ditmars%20-elmhurst%20-ridgewood%20-kew%20-forest%20-corona%20-woodside%20-jackson%20-flushing&srchType=A&format=rss":
         (
             #RegexFilter("(((2[8-9]|3[04-9])th|31st|32nd|33rd).)|((2[8-9]|3[0-9]).?st)"),
             RegexFilter('broadway|((30(th)?|31(st)?) ave)'),
             InverseRegexFilter('[4-9][0-9].{0,4}st'),
             InverseRegexFilter('(1[0-9]|2[0-6]).{0,4}st'),
             InverseRegexFilter('2[458](th)?\s*ave'),
             InverseRegexFilter('available\s*june'),
         )
         }
