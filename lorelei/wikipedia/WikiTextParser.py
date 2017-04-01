import io
import re
import codecs

begin_re = re.compile("<doc .*>$")
end_re = re.compile("^</doc>$")

def get_next_article(source):
    """
    Returns a unicode object containing the next article
    in the given TextIO object
    """
    header = source.readline().strip()
    if not header:
        return None
    if not begin_re.match(header):
        raise Exception("Unexpected header {}".format(header))

    lines = []

    while True:
        line = source.readline()
        if end_re.match(line):
            break

        lines.append(line)

    return ''.join(lines)


def get_all_articles(source):
    """
    Given a path string or a TextIO object, returns an array of the
    text of all articles in that file
    """
    string_arg = False

    if isinstance(source, basestring):
        source = codecs.open(source, 'r', encoding='utf-8')
        string_arg = True

    articles = []

    while True:
        art = get_next_article(source)
        if not art:
            break

        articles.append(art)

    if string_arg:
        source.close()

    return articles
