import datetime
import htmlentitydefs
import re
import rfc822


def parsedate(datestr):
    # Convert a date string to a datetime object.
    # Timezone is ignored. (UTC assumed)
    rfc_tuple = rfc822.parsedate_tz(datestr)
    return datetime.datetime(*rfc_tuple[:7])


def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.

    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is

    return text and unicode(re.sub("&#?\w+;", fixup, text))

