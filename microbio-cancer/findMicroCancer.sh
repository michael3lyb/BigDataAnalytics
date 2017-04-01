#!/bin/bash
for FILE in $(find /mnt/pubmed-all -iname "*cancer*") ; do
	cp $FILE /mnt/pubmed-sub/cancer
done	

for FILE in $(find /mnt/pubmed-all -iname "*microbiol*") ; do
	cp $FILE /mnt/pubmed-sub/microbiol
done	