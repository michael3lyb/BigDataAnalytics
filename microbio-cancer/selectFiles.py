# 721 folders in comm_use.0-9A-B.txt
# 100 files 3.5MB
# when get first 9 file of each folder, there are 160MB
import glob
from shutil import copy
import os
folderlist = glob.glob(r'./*')

dst = "E:\Documents\CMU\Coursework\\11676 big data analysis\snowcrash\microbio-cancer classifier\others"
# print folderlist

# statinfo = os.stat('somefile.txt')
# statinfo.st_size

count = 0
size = 0
for folderName in folderlist:
	i = 0
	filelist = glob.glob(r'./' +folderName+ '/*.txt')
	for filePath in filelist[:9]:
		copy(filePath, dst)
		print filePath
		statinfo = os.stat(filePath)
		size += statinfo.st_size
		count += 1
print count
print str(size/1024/1024) + "MB"
	
	


