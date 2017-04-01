#!/usr/bin/python3
# python CCdownload.py -t 2016-07 -n 1 -f warc

import requests
import argparse
from io import BytesIO
import gzip
import sys

PREFIX = 'https://commoncrawl.s3.amazonaws.com/'
CHUNK_SIZE = 16*1024 # in bytes

# parse the command line arguments
ap = argparse.ArgumentParser()
ap.add_argument("-t", "--time", required=False, default="2016-40",
                help="The time to target ie. 2013-20")
ap.add_argument("-n", "--number", required=False, default=0,
                help="The number of files to download ie. 10, default will download all files")
ap.add_argument("-f", "--files", required=False, default="all",
                help="The type of files to download ie. 'warc', 'wat' or 'wet', default or 'all' will download all formats")

args = vars(ap.parse_args())
time = args['time']
number = int(args['number'])
file_type = args['files']

def download_large_gzip(url):
    local_filename = url.split('/')[-1]

    headers = requests.head(url)
    size = int(headers.headers.get('Content-Length', 0))
    print("Downloading {:.2f}MB".format(size/(1024*1024)))

    r = requests.get(url, stream=True, timeout=5)

    if not r.ok:
        print("HTTP request error")
        print(r.headers)

    i_chunk = 1
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                sys.stdout.flush()

                if i_chunk % 16 == 0:
                    print(".", end="")
                if i_chunk % (16*80) == 0:
                    print("{:03.1f}%".format((i_chunk*CHUNK_SIZE)/size*100))

                i_chunk += 1

    print("")

    return local_filename


def file_download(f_type,time,number):
    warcFile = "https://commoncrawl.s3.amazonaws.com/crawl-data/CC-MAIN-%s/%s.paths.gz" % (time,f_type)
    resp = requests.get(warcFile)
    print("Got {} index".format(f_type))
    
    # The page is stored compressed (gzip) to save space
    # We can extract it using the GZIP library
    raw_data = BytesIO(resp.content)
    f = gzip.GzipFile(fileobj=raw_data)
    data = f.read().decode('utf-8')
    
    # if don't set number, set to row number of the metadata
    if number <= 0:
        number = len(data)
        print("Downloading all {} files".format(number))
    
    i = 0
    
    for line in data.split('\n'):
        line = line.strip()
        print("downloading: " + line)
        download_large_gzip(PREFIX + line)
        i += 1
        if i >= number:
            break

# Call the function file_download based on the arguments		
if file_type.lower() == "all":
    file_download("warc",time,number)
    file_download("wat",time,number)
    file_download("wet",time,number)
elif file_type.lower() == "warc":
    file_download("warc",time,number)
elif file_type.lower() == "wat":
    file_download("wat",time,number)
elif file_type.lower() == "wet":
    file_download("wet",time,number)
else:
    print ("Incorrect File format")
