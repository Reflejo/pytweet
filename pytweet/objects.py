"""
Twitter Objects representation. Data is normalized to python types.
"""

import sys
from parsers import parsedate, unescape

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

    def __init__(self, dictargs=None, **kwargs):
        kwargs.update(dictargs or {})
        for key, fc in self._transformation.iteritems():
            if isinstance(fc, str):
                fc = getattr(sys.modules[__name__], fc)

            val = fc(kwargs[key]) if key in kwargs and kwargs[key] else None
            setattr(self, key, val)


class TwitterSearchResult(TwitterObject):
    """
    Twitter status representation.
    """
    
    _transformation = {
        'text': unescape,
        'to_user_id': int,
        'to_user': unicode,
        'from_user': unicode,
        'id': int,
        'from_user_id': int,
        'iso_language_code': unicode,
        'source': unicode,
        'profile_image_url': unicode,
        'created_at': parsedate,
    }


class TwitterTrend(TwitterObject):
    """
    Twitter trend representation.
    """

    _transformation = {
        'name': unescape,
        'url': unicode,
        'query': unicode
    }


class TwitterUser(TwitterObject):
    """
    Twitter user representation.
    """
    
    _transformation = {
        'created_at': parsedate,
        'description': unescape,
        'favourites_count': int,
        'followers_count': int,
        'following': bool,
        'friends_count': int,
        'id': int,
        'location': unicode,
        'name': unescape,
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
        'status': 'TwitterStatus',
        'statuses_count': int,
        'time_zone': unicode,
        'url': unicode,
        'utc_offset': int,
    }


class TwitterStatus(TwitterObject):
    
    _transformation = {
        'created_at': parsedate,
        'id': int,
        'text': unescape,
        'source': unicode,
        'truncated': bool,
        'in_reply_to_status_id': int,
        'in_reply_to_user_id': int,
        'favorited': bool,
        'in_reply_to_screen_name': unicode,
        'user': TwitterUser,
    }
