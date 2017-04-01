
# coding: utf-8

# # Wikipedia Naive Bayes pipeline in PySpark
# 
# 

# Import python3 goodies and create the spark session

# In[1]:

from __future__ import division, print_function
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
SparkContext.setSystemProperty('spark.executor.memory', '3g')
SparkContext.setSystemProperty('spark.storage.memoryFraction', '0.2')


# Filter to remove empty lines and file structure

# In[2]:

import re

begin_re = re.compile("<doc [^>]*>")
punct_re = re.compile(r'[^\w\s]', re.UNICODE)

def remove_syntax(line):
    line = line.strip()
    line = begin_re.sub('', line)
    line = punct_re.sub('', line)
    
    return line


# (I removed the custom punctuation stripper since a Pipeline containing custom Python transformers can't be persisted, which is a pain overall.)

# In[3]:

exclusion_list = ["lawiki", 'aawiki', 'krwiki', 'hzwiki']
langs = [l for l in os.listdir("wp-data") if l not in exclusion_list]
# langs = ['simplewiki', 'chwiki', 'sowiki'] 
num_langs = len(langs)


# In[4]:

from pyspark.sql.types import StructType, StructField, DoubleType, StringType
schema = StructType([
    StructField("fullText", StringType(), True), StructField("lang", StringType(), False)
])

def load_lang(lang_name):
    file_names = "wp-data/{}/*/wiki_*".format(lang_name)
    text_files = spark.sparkContext.newAPIHadoopFile(file_names, "org.apache.hadoop.mapreduce.lib.input.TextInputFormat",
            "org.apache.hadoop.io.LongWritable", "org.apache.hadoop.io.Text",
            conf={"textinputformat.record.delimiter": "</doc>\n"}).map(lambda l:l[1])
    return text_files.map(remove_syntax).map(lambda l: (l, lang_name)).toDF(schema)


# Loading and preprocessing

# In[5]:

training_articles = spark.createDataFrame([], schema)
testing_articles = spark.createDataFrame([], schema)

test_ratio = 0.2

for lang in langs:
    lang_training, lang_testing = load_lang(lang).randomSplit([1-test_ratio, test_ratio])
    training_articles = training_articles.unionAll(lang_training)
    testing_articles = testing_articles.unionAll(lang_testing)
    
print("{} languages loaded. {} training articles, {} testing articles".format(len(langs),
                                                                              training_articles.count(),
                                                                              testing_articles.count()))


# The following is a workaround for pyspark not finding numpy, [taken from the GitHub issue](https://github.com/jupyter/docker-stacks/issues/109).

# In[6]:

import os, sys

os.environ['PYTHONPATH'] = ':'.join(sys.path)


# In[7]:

from pyspark.ml.feature import CountVectorizer, Tokenizer, StringIndexer, NGram, VectorAssembler
from pyspark.ml.classification import NaiveBayes, RandomForestClassifier, DecisionTreeClassifier
from pyspark.ml import Pipeline  

tokenizer = Tokenizer(inputCol="fullText", outputCol="words")
ng = NGram(inputCol="words", outputCol="bigrams", n=2)
cv = CountVectorizer(inputCol="words", outputCol="wordsCountVector")
cv_ng = CountVectorizer(inputCol="bigrams", outputCol="bigramsCountVector")
fc = VectorAssembler(inputCols=["wordsCountVector", "bigramsCountVector"], outputCol="ngramsCountVector")
si = StringIndexer(inputCol="lang", outputCol="langId")
nb = NaiveBayes(featuresCol="ngramsCountVector", labelCol="langId", modelType="multinomial")
rf = DecisionTreeClassifier(featuresCol="wordsCountVector", labelCol="langId")

pipeline = Pipeline(stages=[tokenizer, ng, cv, cv_ng, fc, si, rf])


# Train the model and save it for later use

# In[8]:

model_nb = pipeline.fit(training_articles)
# model_rf = pipeline_rf.fit(training_articles) # not enough RAM


# In[10]:

import shutil
#shutil.rmtree("model_ng.save")
model_nb.save("model_ng.save")


# Run the classifier on the test sets

# In[11]:

tf = model_nb.transform(testing_articles)


# Get the prediction matrix and save it to a csv file

# In[12]:

matrix = tf.groupBy("langId", "prediction").count().collect()
total_articles = tf.groupBy("langId").count().collect()


# Also, get the langId -> lang matches. Note that if there were empty wikis, they won't appear in `langIDs`.

# In[13]:

langIDs = sorted(set([(i[0], str(i[1])) for i in tf.select("langId", "lang").collect()]), key=lambda x: x[0])


# In[14]:

print(set(map(lambda e: e[1], langIDs)).symmetric_difference(set(langs)))


# In[15]:

import numpy as np
import csv

results_mat = np.zeros((len(langs), len(langs)))
for row in matrix:
    results_mat[int(row.langId),int(row.prediction)] = row["count"]
        
with open("prediction_matrix_ng.csv", "w") as output_file:
    writer = csv.writer(output_file)
    writer.writerow(["v lang / prediction ->"] + list(map(lambda e: e[1], langIDs)))
    for i, (i_lang, lang_name) in enumerate(langIDs):
        writer.writerow([lang_name] + list(results_mat[int(i_lang)]))


# In[ ]:



