#!/bin/bash
for FOLDER in $(ls /mnt/pubmed-AF) ; do
	echo $FOLDER
	cat /mnt/pubmed-AF/$FOLDER/*.txt >> /mnt/pubmed-AF-combine/$FOLDER.txt
done