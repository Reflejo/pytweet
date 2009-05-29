import datetime
import htmlentitydefs
import re
import rfc822

def parse_iso8601(datestr):
    date = datestr.split(' ')
    year, month, day = map(int, date[0].split('-', 3))
    if len(date) == 2:
        time = map(int, date[1].split(':', 3))
        if len(time) == 3:
            hours, minutes, seconds = time
        else:
            hours, minutes = time
            seconds = 0
    else:
        hours, minutes, seconds = 0, 0 ,0

    return datetime.datetime(year, month, day, hours, minutes, seconds)

def parsedate(datestr):
    # Convert a date string to a datetime object.
    # Timezone is ignored. (UTC assumed)
    rfc_tuple = rfc822.parsedate_tz(datestr)
    return datetime.datetime(*rfc_tuple[:7])


def unescape(text, encoding="UTF-8"):
    """
    Removes HTML or XML character references and entities from a text string.

    @param text The HTML (or XML) source text.
    @return The unescaped text as a Unicode.
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    text = unichr(int(text[3:-1], 16))
                else:
                    text = unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass

        return text

    # Decode string as needed
    text = text.decode(encoding) if isinstance(text, str) else text 
    return text and re.sub("&#?\w+;", fixup, text)
