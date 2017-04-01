from __future__ import print_function

import warc
import sys

if len(sys.argv) != 2:
    print("Usage: {} <input_file>".format(sys.argv[0]))
    sys.exit(0)

f = warc.open(sys.argv[1])
for record in f:
    print(record.url)
    # record.header => Dictionary containing the header field names and their values
    # record.payload => Payload object, can be read with a.payload.read()


