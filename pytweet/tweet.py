#
# Copyright 2009 Kodear. All Rights Reserved.
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

"""
A pythonic library that provides a simple interface to the Twitter API.
Oh, and values are normalized to python types.
"""

import simplejson
import urllib, urllib2
import urlparse
from objects import TwitterUser, TwitterStatus
from setobjects import TwitterTrendSet, TwitterUserSet, TwitterStatusSet, \
                       TwitterSearchResultSet

__author__ = 'Martin Conte Mac Donell <Reflejo@gmail.com>'
__version__ = '0.1-beta'

ENCODING = 'utf8'
API_DOMAIN = 'twitter.com'
SEARCH_API_DOMAIN = 'search.twitter.com'

DATEDAILY = 'daily'
DATEWEEKLY = 'weekly'
DATECURRENT = 'current'
SOCKET_TIMEOUT = 10

class TwitterError(Exception):
    """Base class for Twitter errors"""
  
    @property
    def message(self):
        """Returns the first argument used to construct this error."""
        return self.args[0]


class ConnectionError(TwitterError):
    """Network related errors"""

    def __init__(self, message, code=None):
        self.code = code
        super(ConnectionError, self).__init__(message)


def authenticated(func):
    """
    Decorator for methods that need authentication
    """
    def _newf(*args, **kw):
        instance = args[0]
        if not instance.is_authenticated():
            raise TwitterError('You must call authenticate first')

        return func(*args, **kw)
    return _newf


class Twitter(object):
    """
    Main Twitter API. 

    Usage:

    To create an instance of the twitter.Api class, with no authentication:

      >>> import pytweet
      >>> api = pytweet.Twitter()

    See each method for more information.
    """

    def __init__(self, username=None, password=None):
        self._auth_header = ()
        if username and password:
            self.authenticate(username, password)

        # This is the only way we can prevent socket hangs.
        urllib2.socket.setdefaulttimeout(SOCKET_TIMEOUT)

    def is_authenticated(self):
        """
        If auth_header has data we asume that API is authenticated

        >>> api = Twitter(username='testpy', password='testpy')
        >>> api.is_authenticated()
        True

        """
        return bool(self._auth_header)

    def authenticate(self, username, password):
        """
        Just keep authenticate information. We will use it in next posts.
        """
        baseauth = '%s:%s' % (username, password)
        authheader =  "Basic %s" % baseauth.encode('base64').strip()
        self._auth_header = ("Authorization", authheader)

    def _parse_response(self, response):
        # Parse JSON response.
        parsed = simplejson.loads(response)

        if not parsed:
            raise TwitterError("Empty response from twitter")

        # Check if there is any error in response
        if 'error' in parsed:
            raise TwitterError(parsed['error'])

        return parsed

    def _fetchurl(self, uri, domain=None, post_data=None, get_data=None):
        # Fetch a URL.
        #
        # @uri: The uri to retrive
        # @domain: Twitter domain API. [optional]
        # @post_data: If set, POST will be used and this dictionary will be 
        #             included as parameters. [optional]
        # @get_data: A dictionary which will be encoded and added to query 
        #            string. [optional]
        #
        # Returns: A parsed response or raise an error if field 
        #          'error' is found.

        # Make it iterable if it's not :-)
        post_data = post_data or {}
        get_data = get_data or {}

        # Reduce dictionary. Remove empty values.
        post_data = dict([(k, v) for k, v in post_data.iteritems() if v])
        get_data = dict([(k, v) for k, v in get_data.iteritems() if v])
 
        # craft url
        uri = "%s?%s" % (uri, urllib.urlencode(get_data)) if get_data else uri
        url = urlparse.urljoin("http://%s" % (domain or API_DOMAIN), uri)

        if isinstance(url, unicode):
            url = url.encode(ENCODING)

        req = urllib2.Request(url)
        post_data = urllib.urlencode(post_data) or None
        
        if self._auth_header:
            req.add_header(*self._auth_header)
    
        try:
            handle = urllib2.urlopen(req, post_data)
        except urllib2.URLError, e:
            ce = ConnectionError("Network error (%s)" % str(e))
            ce.code = getattr(e, 'code', None)
            raise ce

        return self._parse_response(handle.read())

    def _rate_remaining(self):
        """
        Returns the remaining number of API requests available to the
        requesting user before the API limit is reached for the current hour.
        Calls to rate_limit_status do not count against the rate limit.  
        If authentication credentials are provided, the rate limit status 
        for the authenticating user is returned.  Otherwise, the rate limit
        status for the requester's IP address is returned.

        >>> rate = api.rate_remaining
        150

        """
        uri = '/account/rate_limit_status.json'
        res = self._fetchurl(uri)
        return res['remaining_hits']

    rate_remaining = property(_rate_remaining)

    def search(self, query, since_id=None, lang=None, geocode=None):
        """
        Returns tweets that match a specified query.

        @lang: Restricts tweets to the given language, given by an 
               ISO 639-1 code. [optional]
        @since_id: Returns tweets with status ids greater than the given 
                   id. [optional]
        @geocode: Returns tweets by users located within a given radius 
                  of the given latitude/longitude, where the user's location 
                  is taken from their Twitter profile. The parameter value is
                  specified by "latitide,longitude,radius", where radius 
                  units must be specified as either "mi" (miles) or 
                  "km" (kilometers). [optional]

        >>> search = api.search('from:testpy') # Data is not fetched
        >>> res = search[:10] # Data is fetched and cached.
        >>> res[0].text
        u'Big success!'
        >>> res[0].from_user
        u'testpy'
        >>> res[0].created_at
        datetime.datetime(2009, 5, 29, 3, 46, 6)

        """
        uri = '/search.json'
        return TwitterSearchResultSet(self._fetchurl, uri, 
                                      domain=SEARCH_API_DOMAIN,
                                      query=query, lang=lang, geocode=geocode,
                                      since_id=since_id)

    def trends(self, exclude_hash=False, date=None, by=DATECURRENT):
        """
        Returns the top ten topics that are currently trending on Twitter.
        The response includes the time of the request, the name of each trend,
        and the url to the Twitter Search results page for that topic.

        >>> for date, trends in api.trends().iteritems():
        ...     trends[0]
        <pytweet.objects.TwitterTrend object at 0x...>
        
        """
        assert by in (DATECURRENT, DATEDAILY, DATEWEEKLY), \
            "Invalid by parameter, should be DATECURRENT, DATEDAY or DATEWEEK"

        uri = '/trends/%s.json' % by
        data = {
            'exclude': "hashtags" if exclude_hash else None,
            'date': date,
        }
        return TwitterTrendSet(self._fetchurl(uri=uri, post_data=data,
                                              domain=SEARCH_API_DOMAIN))


    def user(self, user):
        """
        Returns extended information of a given user, specified by ID or
        screen name. The author's most recent status will be included.

        >>> user = api.user('testpy')
        >>> user.name
        u'pytweet'
        >>> user.status.text
        u'Big success!'
        >>> user.status.created_at
        datetime.datetime(2009, 5, 29, 3, 46, 6)

        """
        uri = '/users/show/%s.json' % user
        return TwitterUser(**self._fetchurl(uri))

    @authenticated
    def followers(self, user=None):
        """
        Returns the authenticating user's followers, each with current 
        status inline.  They are ordered by the order in which they 
        joined Twitter

        >>> for user in api.followers('testpy'):
        ...     user.name, user
        ... 
        (u'Atommica Cheat', <pytweet.objects.TwitterUser object at 0x...>)

        """
        uri = '/statuses/followers.json'
        return TwitterUserSet(self._fetchurl, uri, user=user)

    @authenticated
    def friends(self, user=None):
        """
        Returns a user's friends, each with current status. They are
        ordered by the order in which they were added as friends. Defaults to
        the authenticated user's friends. It's also possible to request
        another user's friends list via the user parameter.

        >>> for user in api.friends('testpy'):
        ...     user.name
        ...     user
        ...     user.status
        ... 
        u'Reflejo'
        <pytweet.objects.TwitterUser object at 0x...>
        <pytweet.objects.TwitterStatus object at 0x...>

        """
        uri = '/statuses/friends.json'
        return TwitterUserSet(self._fetchurl, uri, user=user)

    @authenticated
    def destroy(self, id):
        """
        Destroys the status specified by the required ID parameter.
        The authenticating user must be the author of the specified status.

        >>> api.destroy(12345)
        <pytweet.objects.TwitterStatus object at 0x...>

        """
        uri = '/statuses/destroy/%d.json' % id
        data = {'delete': '1'}
        return TwitterStatus(**self._fetchurl(uri, post_data=data))

    def user_timeline(self, user=None):
        """
        Returns the most recent user's timeline via the id parameter. 
        This is the equivalent of the Web /<user> page for your own user, 
        or the profile page for a third party.

        >>> statuses = api.user_timeline('Reflejo')
        >>> for status in api.user_timeline('testpy'):
        ...     status.text
        ...     status
        ... 
        u'Big success!'
        <pytweet.objects.TwitterStatus object at 0x...>

        """
        if not user and not self.is_authenticated():
            raise TwitterError("This method requires authentication if user " \
                               "is not supplied")

        uri = '/statuses/user_timeline.json'
        return TwitterStatusSet(self._fetchurl, uri, user=user)
