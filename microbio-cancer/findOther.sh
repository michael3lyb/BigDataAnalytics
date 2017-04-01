#!/bin/bash
for FOLDER in $(ls /mnt/pubmed-all) ; do
	#echo $FOLDER
	if echo $FOLDER | grep -iq cancer; then
		echo "find cancer"
		continue
	fi
	if echo $FOLDER | grep -iq microbiol; then
		echo "find microbiol"
		continue
	fi
	COUNT=0
	for FILE in $(ls /mnt/pubmed-all/$FOLDER) ; do
		COUNT=$((COUNT+1))
		#echo /mnt/pubmed-all/$FOLDER/$FILE 
		cp /mnt/pubmed-all/$FOLDER/$FILE /mnt/pubmed-sub/other
	    if [ "$COUNT" -gt 4 ]; then
	        #echo $COUNT
	        break
	    fi
	done
done