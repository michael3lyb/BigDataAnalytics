# Gets the sizes in MB for all wikipedias specified in the <wikipedia-list> parameter.

import requests
import sys

def make_dump_url(lang):
    return "https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-pages-articles-multistream.xml.bz2".format(lang)

if len(sys.argv) != 2:
    print("Usage: {} <wikipedia-list>".format(sys.argv[0]))
    sys.exit(0)

total_size = 0
total_wikis = 0
errors = 0

with open(sys.argv[1], 'r') as wikipedia_list:
    for line in wikipedia_list:
        lang = line.strip()
        if not line:
            continue

        total_wikis += 1
        r = requests.head(make_dump_url(lang))
        if not r.ok:
            errors += 1
            print("Could not download dump for {}".format(lang))
        else:
            size = int(r.headers['Content-Length'])
            print("{:<10}: {: >5}".format(lang, int(size)))
            total_size += size

print("Pinged {} wikis ({} ok, {} errors). Total size {} MB.".format(total_wikis, total_wikis-errors, errors, int(total_size)/(1024*1024)))

