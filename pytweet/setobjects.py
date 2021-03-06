"""
Twitter Objects Set. Here we define objects that can return more than
one result taking care of pagination logic.
"""

import math
from parsers import parse_iso8601
from datetime import datetime
from objects import TwitterUser, TwitterStatus, TwitterTrend, \
                    TwitterSearchResult

ITEMS_PER_PAGE = 100

#########################################################
# Status Set
#########################################################
class PaginationSet(object):
    """
    Pagination set it's a lazy bunch of data: url is retrived only 
    when resultset is sliced.

    params are:
        fetch: callback function to fetch url
        uri: URI for request
        kwargs: depends on Pagination class. usually will 
                use domain and since_id
    """

    resultclass = None

    def __init__(self, fetch, uri, **kwargs):
        self._fetch = fetch
        self.uri = uri
        self.domain = kwargs.pop('domain', None)
        self.since_id = kwargs.pop('since_id', 0)
        
        # Defaults
        self._results = []
        self._actualidx = 0

        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    def _fill_metadata(self, metadata):
        # Fill some results metadata as needed
        pass

    def _get_data(self, page):
        # Make the dict for HTTP POST request
        pass

    def _get_results(self, result):
        # Get result with some criteria like a dict key or something.
        # By default we just return given list.
        return result

    def _fetch_results(self, offset):
        page = int(math.ceil(offset / ITEMS_PER_PAGE)) + 1
        data = self._get_data(page)

        # Fill results with empty values. This is done because user can slice
        # a distance of more than one page for example results[10000:10010]
        fill_amount = (page - 1) * ITEMS_PER_PAGE
        for i in xrange(len(self._results), fill_amount):
            self._results.append(None)

        result = self._fetch(self.uri, get_data=data,
                             domain=self.domain)
        results = self._get_results(result)
        results_count = len(results)
        for i in xrange(ITEMS_PER_PAGE):
            add = '' if i >= results_count else self.resultclass(**results[i])

            # There is a bug in twitter API. You cannot use max_id 
            # and since_id together. See:
            # http://code.google.com/p/twitter-api/issues/detail?id=486
            if hasattr(add, 'id') and add.id <= self.since_id:
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
        return self

    def next(self):
        """
        Get next iteration item. We just iterate results until end or
        first '' occurrence.
        """
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
            limit = (k.stop - offset) if k.stop is not None else ITEMS_PER_PAGE
        else:
            offset = k
            limit = 1

        while True:
            # Check if some result is None or if result is smaller than 
            # requested index.
            end = offset + limit

            is_smaller = limit > 0 and (len(self._results) < end)
            has_empty = not is_smaller and None in self._results[offset:end]

            if not is_smaller and not has_empty:
                break

            # if we got less results that per_page we are done.
            fetch_total = self._fetch_results(offset)
            if fetch_total < ITEMS_PER_PAGE:
                break

            offset = len(self._results)
            limit -= fetch_total

        if isinstance(k, slice):
            return [res for res in self._results[k] if res != '']
        else:
            return self._results[k] or None


class TwitterUserSet(PaginationSet):
    """
    User result set. It's a lazy bunch of users. 
    """

    resultclass = TwitterUser

    def _get_data(self, page):
        return {
            'page': page,
            'user': self.user
        }


class TwitterTrendSet(dict):
    """
    Trends are an especial case of sets since they don't need pagination.
    """

    def __init__(self, results):
        self.as_of = datetime.fromtimestamp(int(results['as_of']))
        
        for dat, trends in results['trends'].iteritems():
            dat = parse_iso8601(dat)
            for trend in trends:
                self.setdefault(dat, []).append(TwitterTrend(**trend))


class TwitterSearchResultSet(PaginationSet):
    """
    Status result set. It's a lazy bunch of search results. 
    """

    resultclass = TwitterSearchResult

    def __init__(self, *args, **kwargs):
        self.max_id = 0
        super(TwitterSearchResultSet, self).__init__(*args, **kwargs)

    def _fill_metadata(self, metadata):
        self.completed_in = metadata['completed_in']
        self.max_id = max(self.max_id, metadata['max_id'])

    def _get_results(self, result):
        return result['results']

    def _get_data(self, page):
        return {
            'q': self.query,
            'page': page,
            'rpp': ITEMS_PER_PAGE,
            'since_id': self.since_id if not self.max_id else None,
            'lang': self.lang,
            'max_id': self.max_id,
            'geocode': self.geocode,
        }


class TwitterStatusSet(PaginationSet):
    """
    Status result set. It's a lazy bunch of statuses. 
    """

    resultclass = TwitterStatus

    def __init__(self, *args, **kwargs):
        self.max_id = 0
        super(TwitterStatusSet, self).__init__(*args, **kwargs)

    def _get_data(self, page):
        return {
            'page': page,
            'count': ITEMS_PER_PAGE,
            'since_id': self.since_id if not self.max_id else None,
            'screen_name': self.user,
            'max_id': self.max_id,
        }
