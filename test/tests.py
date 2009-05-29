import doctest
from pytweet import Twitter

api = Twitter(username='testpy', password='testpy')
globs = {
    'Twitter': Twitter,
    'api': api
}
doctest.testfile('../pytweet/tweet.py', globs=globs, 
                 optionflags=doctest.ELLIPSIS)
