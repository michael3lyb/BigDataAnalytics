# Project SnowCrash 
## 11676 - Big Data Analytics

Tools: Apache Spark (MLlib), Python, AWS

Data : CommonCrawl, Wikipedia, PubMed

This project contains: 

- code (CCdownload.py) for downloading CommonCrawl data from Amazon S3 as specified on the [CommonCrawl website](http://commoncrawl.org/the-data/get-started/).
- lorelei: a language classifier based on CommonCrawl.
- bioExtractor: a  binary classifier to extract all bio-related article from CommonCrawl. Training on PubMed data. 
- microbio-cancer: a classifier to distinguish Microbiology article, Cancer artile and others. 

Did ETL jobs on PubMed and Common Crawl data using Spark (Python).  Load and transform WET files as Spark Dataframe.

Built a bio-related article classifier based on PubMed data by using Naive Bayes and Logistic Regression(MLlib).