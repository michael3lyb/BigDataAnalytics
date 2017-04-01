#!/bin/bash

for FILE in $(ls compressed) ; do
    LANGUAGE=$(echo $FILE | cut -d'-' -f1)
    if [ -d "uncompressed/$LANGUAGE" ]; then
        continue
    fi
    bunzip2 -c -k "compressed/$FILE" > current.xml
    wikiextractor/WikiExtractor.py current.xml -o "uncompressed/$LANGUAGE"
    rm current.xml
done

