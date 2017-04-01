# Plan of action for LORELEI classification

I think we can use a naive bayes classifier for language recognition: it's fast to train and use, and should work rather well given that words fairly often exist in only one language and that we have lots of training data thanks to Wikipedia.

## The Wikipedia dataset

Wikipedia provides different kinds of dumps. They're either SQL dumps or XML documents; I assume we'll use the latter, since the cost of loading a multi-gigabyte dump into an SQL database is high. Dumps can be accessed at `https://dumps.wikimedia.org/<lang>wiki/latest/`. The dump of most interest to us seems to be `<lang>wiki-latest-pages-articles-multistream.xml.bz2`, which contains the text of all pages in a single (compressed) XML file. This includes articles, as well as template pages, talk pages, user pages, etc. However, the type of pages is clearly marked so articles should be easy to extract.

There are 295 languages, for a total of 42,000,000 articles. The size of Wikipedias vary wildly, with 49 Wikipedias under 1000 articles and 112 between 1000 and 10000 articles. [The stats are available here](http://wikistats.wmflabs.org/display.php?t=wp). The compression ratio of the dumps is about 1/5, and the total size of the compressed dumps for all 295 languages is 53GB, or about 264GB of uncompressed XML data.

The rate is throttled by Wikimedia to about 2MB/s per connection and two connections per IP, which adds up to around 3 hours 45 minutes of downloading.

## Preprocessing

The main preprocessing problem is converting MediaWiki markup to plain text. This looks like it can be done using [this tool](http://medialab.di.unipi.it/wiki/Wikipedia_Extractor) ([GitHub](https://github.com/attardi/wikiextractor)) seems up-to-date and functional. I was able to make it work on the Latin wiki dump, and it took about 5 minutes to run. This generates expanded articles embedded in an extremely simple XML structure, and split into ~1MB files.

I wrote a small Python library to read the produced files.

[Other tools are listed on the Wikimedia website](https://meta.wikimedia.org/wiki/Data_dumps/Other_tools).

## Spark pipeline

### Training

  1. Create a DataFrame from the entire Wikipedia collection, filtering doc lines.
  2. Use a `PunctuationStripper` (custom transformer) and a `Tokenizer` to tokenize the text correctly.
  3. Use a [`CountVectorizer`](https://spark.apache.org/docs/latest/ml-features.html#countvectorizer) to turn the articles into count vectors.
  4. Fit a (multinomial) [`NaiveBayes`](https://spark.apache.org/docs/latest/ml-classification-regression.html#naive-bayes) model on the resulting DataFrame.

I have implemented a demo of this pipeline [in a jupyter notebook](lorelei/wikipedia/spark-wikipedia.ipynb).