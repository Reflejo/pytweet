"""
A pythonic library that provides a simple interface to the Twitter API.
Oh, and values are normalized to python types.
"""

from tweet import Twitter, TwitterError, ConnectionError

__all__ = ['Twitter', 'TwitterError', 'ConnectionError']
