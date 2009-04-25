"""
Twitter Objects representation. Data is normalized to python types.
"""

import math
from parsers import parsedate, unescape

SEARCH_API_DOMAIN = 'search.twitter.com'

#########################################################
# Basic Objects
#########################################################
class TwitterObject(object):
    """
    Common base object. Takes a dictionary and set an attribute for each key
    normalizing values using _transformation dict.

    For example: {'name': 'Reflejo', 'age': '25'}
    Will be translated to: 
        object.name = u'Reflejo'
        object.age = 25
    """
    
    _transformation = {}

    def __init__(self, dictargs={}, **kwargs):
        kwargs.update(dictargs)
        for key, fc in self._transformation.iteritems():
            val = fc(kwargs[key]) if key in kwargs and kwargs[key] else None
            setattr(self, key, val)


class TwitterStatus(TwitterObject):
    
    _transformation = {
        'text': unescape,
        'to_user_id': int,
        'from_user': unicode,
        'id': int,
        'from_user_id': int,
        'iso_language_code': unicode,
        'source': unicode,
        'profile_image_url': unicode,
        'created_at': parsedate,
    }


class TwitterUser(TwitterObject):
    
    _transformation = {
        'created_at': parsedate,
        'description': unescape,
        'favourites_count': int,
        'followers_count': int,
        'following': bool,
        'friends_count': int,
        'id': int,
        'location': unicode,
        'name': unicode,
        'notifications': bool,
        'profile_background_color': unicode,
        'profile_background_image_url': unicode,
        'profile_background_tile': bool,
        'profile_image_url': unicode,
        'profile_link_color': unicode,
        'profile_sidebar_border_color': unicode,
        'profile_sidebar_fill_color': unicode,
        'profile_text_color': unicode,
        'protected': bool,
        'screen_name': unicode,
        'status': TwitterStatus,
        'statuses_count': int,
        'time_zone': unicode,
        'url': unicode,
        'utc_offset': int,
    }


#########################################################
# Status Set
#########################################################
class TwitterStatusSet(object):
    """
    Status result set. It's a lazy banch of statuses. url is retrived only 
    when resultset is sliced.
    """

    def __init__(self, api, query, per_page=100, since_id=None, lang=None, 
                 geocode=None):
        self._api = api
        self.query = query
        self.per_page = per_page
        self.since_id = since_id
        self.lang = lang
        self.geocode = geocode
        self.max_id = None
        self._results = []

    def _fill_metadata(self, metadata):
        self.completed_in = metadata['completed_in']
        self.max_id = max(self.max_id, metadata['max_id'])

    def _fetch_results(self, offset):
        page = int(math.ceil(offset / self.per_page)) + 1
        data = {
            'q': self.query,
            'page': page,
            'rpp': self.per_page,
            'since_id': self.since_id if not self.max_id else None,
            'lang': self.lang,
            'max_id': self.max_id,
            'geocode': self.geocode,
        }

        # Fill results with empty values. This is done because user can slice
        # a distance of more than one page for example results[10000:10010]
        fill_amount = (page - 1) * self.per_page
        for i in xrange(len(self._results), fill_amount):
            self._results.append(None)

        result = self._api._fetchurl('/search.json', get_data=data,
                                     domain=SEARCH_API_DOMAIN)
        results = result.pop('results')
        results_count = len(results)
        for i in xrange(self.per_page):
            add = '' if i >= results_count else TwitterStatus(**results[i])

            # There is a bug in twitter API. You cannot use max_id 
            # and since_id together. See:
            # http://code.google.com/p/twitter-api/issues/detail?id=486
            if add and add.id <= self.since_id:
                results_count = i
                add = ''

            if len(self._results) > offset:
                self._results[offset] = add
            else:
                self._results.append(add)

            offset += 1

        self._fill_metadata(result)
        return results_count

    def __len__(self):
        raise Exception("I can't tell you D:")

    def __iter__(self):
        self._actualidx = 0
        return self

    def next(self):
        res = None
        try:
            res = self[self._actualidx]
            self._actualidx += 1
        except IndexError:
            pass

        if not res:
            raise StopIteration

        return res

    def __getitem__(self, k):
        # Retrieve an item or slice from the set of results.
        if not isinstance(k, (slice, int, long)):
            raise TypeError("ResultSet indices must be integers")

        # Check slice integrity
        assert (not isinstance(k, slice) and (k >= 0)) \
            or (isinstance(k, slice) and (k.start is None or k.start >= 0) \
            and (k.stop is None or k.stop >= 0)), \
            "Negative indexing is not supported."

        if isinstance(k, slice):
            offset = k.start or 0
            limit = (k.stop - offset) if k.stop is not None else self.per_page
        else:
            offset = k
            limit = 1

        actual = len(self._results)
        while True:
            # Check if some result is None or if result is smaller than 
            # requested index.
            end = offset + limit
            is_smaller = limit > 0 and (len(self._results) < end)
            has_empty = not is_smaller and None in self._results[offset:end]

            if not is_smaller and not has_empty:
                break

            # if we got less results that per_page we are done.
            if self._fetch_results(offset) < self.per_page:
                break

            offset = len(self._results)
            limit -= (offset - actual)

        if isinstance(k, slice):
            return [res for res in self._results[k] if res != '']
        else:
            return self._results[k] or None
