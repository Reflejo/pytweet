#
# Copyright 2009 Atommica. All Rights Reserved.
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
from objects import TwitterSearchResultSet, TwitterUser, TwitterUserSet, \
                    TwitterStatus, TwitterStatusSet

__author__ = 'Martin Conte Mac Donell <Reflejo@gmail.com>'
__version__ = '0.1-beta'

API_DOMAIN = 'twitter.com'
SEARCH_API_DOMAIN = 'search.twitter.com'

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
        self.code =code
        super(ConnectionError, self).__init__(message)


# Decorator for authenticated methods
def authenticated(func):
    def newf(*args, **kw):
        instance = args[0]
        if not instance.is_authenticated():
            raise TwitterError('You must call authenticate first')

        return func(*args, **kw)
    return newf


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
        return bool(self._auth_header)

    def authenticate(self, username, password):
        # Just keep authenticate information. We will use it in next posts.
        baseauth = '%s:%s' % (username, password)
        authheader =  "Basic %s" % baseauth.encode('base64').strip()
        self._auth_header = ("Authorization", authheader)

    def _parse_response(self, response):
        # Parse JSON response.
        parsed = simplejson.loads(response)

        # Check if there is any error in response
        if 'error' in parsed:
            raise TwitterError(data['error'])
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

    def user(self, user):
        """
        Returns extended information of a given user, specified by ID or
        screen name. The author's most recent status will be included.
        """
        uri = '/users/show/%s.json' % user
        return TwitterUser(**self._fetchurl(uri))

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
        """
        uri = '/search.json'
        return TwitterSearchResultSet(self, uri, domain=SEARCH_API_DOMAIN,
                                      query=query, lang=lang, geocode=geocode,
                                      since_id=since_id)

    @authenticated
    def followers(self, user=None):
        """
        Returns the authenticating user's followers, each with current 
        status inline.  They are ordered by the order in which they 
        joined Twitter
        """
        uri = '/statuses/followers.json'
        return TwitterUserSet(self, uri, user=user)

    @authenticated
    def friends(self, user=None):
        """
        Returns the authenticating user's followers, each with current 
        status inline.  They are ordered by the order in which they 
        joined Twitter
        """
        uri = '/statuses/friends.json'
        return TwitterUserSet(self, uri, user=user)

    @authenticated
    def destroy(self, id):
        """
        Destroys the status specified by the required ID parameter.
        The authenticating user must be the author of the specified status.
        """
        uri = '/statuses/destroy/%d.json' % id
        data = {'delete': '1'}
        return TwitterStatus(**self._fetchurl(uri, post_data=data))

    def user_timeline(self, user=None, since_id=None):
        """
        Returns the most recent user's timeline via the id parameter. 
        This is the equivalent of the Web /<user> page for your own user, 
        or the profile page for a third party.
        """
        if not user and not self.is_authenticated():
            raise TwitterError("This method requires authentication if user " \
                               "is not supplied")

        uri = '/statuses/user_timeline.json'
        return TwitterStatusSet(self, uri, user=user)
