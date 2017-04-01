
# Wikipedia Naive Bayes pipeline in PySpark



Import python3 goodies and create the spark session


```python
from __future__ import division, print_function
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
SparkContext.setSystemProperty('spark.executor.memory', '3g')
SparkContext.setSystemProperty('spark.storage.memoryFraction', '0.2')
```

Filter to remove empty lines and file structure


```python
import re

begin_re = re.compile("<doc [^>]*>")
punct_re = re.compile(r'[^\w\s]', re.UNICODE)

def remove_syntax(line):
    line = line.strip()
    line = begin_re.sub('', line)
    line = punct_re.sub('', line)
    
    return line
```

(I removed the custom punctuation stripper since a Pipeline containing custom Python transformers can't be persisted, which is a pain overall.)


```python
exclusion_list = ["lawiki", 'aawiki', 'krwiki', 'hzwiki']
langs = [l for l in os.listdir("wp-data") if l not in exclusion_list]
num_langs = len(langs)
```


```python
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
```

Loading and preprocessing


```python
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
```

    171 languages loaded. 661879 training articles, 165579 testing articles


The following is a workaround for pyspark not finding numpy, [taken from the GitHub issue](https://github.com/jupyter/docker-stacks/issues/109).


```python
import os, sys

os.environ['PYTHONPATH'] = ':'.join(sys.path)
```


```python
from pyspark.ml.feature import CountVectorizer, Tokenizer, StringIndexer, NGram, VectorAssembler
from pyspark.ml.classification import NaiveBayes, RandomForestClassifier
from pyspark.ml import Pipeline  

tokenizer = Tokenizer(inputCol="fullText", outputCol="words")
ng = NGram(inputCol="words", outputCol="bigrams", n=2)
cv = CountVectorizer(inputCol="words", outputCol="wordsCountVector")
cv_ng = CountVectorizer(inputCol="bigrams", outputCol="bigramsCountVector")
fc = VectorAssembler(inputCols=["wordsCountVector", "bigramsCountVector"], outputCol="ngramsCountVector")
si = StringIndexer(inputCol="lang", outputCol="langId")
nb = NaiveBayes(featuresCol="ngramsCountVector", labelCol="langId", modelType="multinomial")
#rf = RandomForestClassifier(featuresCol="wordsCountVector", labelCol="langId")

pipeline = Pipeline(stages=[tokenizer, ng, cv, cv_ng, fc, si, nb])
```

Train the model and save it for later use


```python
model_nb = pipeline.fit(training_articles)
# model_rf = pipeline_rf.fit(training_articles) # not enough RAM
```


```python
import shutil
#shutil.rmtree("model_ng.save")
model_nb.save("model_ng.save")
```


    ---------------------------------------------------------------------------

    Py4JJavaError                             Traceback (most recent call last)

    <ipython-input-10-71fea3f64a11> in <module>()
          1 import shutil
          2 #shutil.rmtree("model_ng.save")
    ----> 3 model_nb.save("model_ng.save")
    

    /Users/matthieu/src/cmu/starzl/spark/spark-2.0.1-bin-hadoop2.7/python/pyspark/ml/pipeline.pyc in save(self, path)
        220     def save(self, path):
        221         """Save this ML instance to the given path, a shortcut of `write().save(path)`."""
    --> 222         self.write().save(path)
        223 
        224     @classmethod


    /Users/matthieu/src/cmu/starzl/spark/spark-2.0.1-bin-hadoop2.7/python/pyspark/ml/util.pyc in save(self, path)
         98         if not isinstance(path, basestring):
         99             raise TypeError("path should be a basestring, got type %s" % type(path))
    --> 100         self._jwrite.save(path)
        101 
        102     def overwrite(self):


    /Users/matthieu/src/cmu/starzl/spark/spark-2.0.1-bin-hadoop2.7/python/lib/py4j-0.10.3-src.zip/py4j/java_gateway.py in __call__(self, *args)
       1131         answer = self.gateway_client.send_command(command)
       1132         return_value = get_return_value(
    -> 1133             answer, self.gateway_client, self.target_id, self.name)
       1134 
       1135         for temp_arg in temp_args:


    /Users/matthieu/src/cmu/starzl/spark/spark-2.0.1-bin-hadoop2.7/python/pyspark/sql/utils.pyc in deco(*a, **kw)
         61     def deco(*a, **kw):
         62         try:
    ---> 63             return f(*a, **kw)
         64         except py4j.protocol.Py4JJavaError as e:
         65             s = e.java_exception.toString()


    /Users/matthieu/src/cmu/starzl/spark/spark-2.0.1-bin-hadoop2.7/python/lib/py4j-0.10.3-src.zip/py4j/protocol.py in get_return_value(answer, gateway_client, target_id, name)
        317                 raise Py4JJavaError(
        318                     "An error occurred while calling {0}{1}{2}.\n".
    --> 319                     format(target_id, ".", name), value)
        320             else:
        321                 raise Py4JError(


    Py4JJavaError: An error occurred while calling o3604.save.
    : java.lang.OutOfMemoryError: Requested array size exceeds VM limit
    	at org.apache.spark.sql.catalyst.expressions.codegen.BufferHolder.grow(BufferHolder.java:73)
    	at org.apache.spark.sql.catalyst.expressions.GeneratedClass$SpecificUnsafeProjection.apply1_2$(Unknown Source)
    	at org.apache.spark.sql.catalyst.expressions.GeneratedClass$SpecificUnsafeProjection.apply(Unknown Source)
    	at org.apache.spark.sql.execution.LocalTableScanExec$$anonfun$1.apply(LocalTableScanExec.scala:38)
    	at org.apache.spark.sql.execution.LocalTableScanExec$$anonfun$1.apply(LocalTableScanExec.scala:38)
    	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
    	at scala.collection.TraversableLike$$anonfun$map$1.apply(TraversableLike.scala:234)
    	at scala.collection.immutable.List.foreach(List.scala:381)
    	at scala.collection.TraversableLike$class.map(TraversableLike.scala:234)
    	at scala.collection.immutable.List.map(List.scala:285)
    	at org.apache.spark.sql.execution.LocalTableScanExec.<init>(LocalTableScanExec.scala:38)
    	at org.apache.spark.sql.execution.SparkStrategies$BasicOperators$.apply(SparkStrategies.scala:393)
    	at org.apache.spark.sql.catalyst.planning.QueryPlanner$$anonfun$1.apply(QueryPlanner.scala:60)
    	at org.apache.spark.sql.catalyst.planning.QueryPlanner$$anonfun$1.apply(QueryPlanner.scala:60)
    	at scala.collection.Iterator$$anon$12.nextCur(Iterator.scala:434)
    	at scala.collection.Iterator$$anon$12.hasNext(Iterator.scala:440)
    	at org.apache.spark.sql.catalyst.planning.QueryPlanner.plan(QueryPlanner.scala:61)
    	at org.apache.spark.sql.execution.SparkPlanner.plan(SparkPlanner.scala:47)
    	at org.apache.spark.sql.execution.SparkPlanner$$anonfun$plan$1$$anonfun$apply$1.applyOrElse(SparkPlanner.scala:51)
    	at org.apache.spark.sql.execution.SparkPlanner$$anonfun$plan$1$$anonfun$apply$1.applyOrElse(SparkPlanner.scala:48)
    	at org.apache.spark.sql.catalyst.trees.TreeNode$$anonfun$transformUp$1.apply(TreeNode.scala:301)
    	at org.apache.spark.sql.catalyst.trees.TreeNode$$anonfun$transformUp$1.apply(TreeNode.scala:301)
    	at org.apache.spark.sql.catalyst.trees.CurrentOrigin$.withOrigin(TreeNode.scala:69)
    	at org.apache.spark.sql.catalyst.trees.TreeNode.transformUp(TreeNode.scala:300)
    	at org.apache.spark.sql.catalyst.trees.TreeNode$$anonfun$4.apply(TreeNode.scala:298)
    	at org.apache.spark.sql.catalyst.trees.TreeNode$$anonfun$4.apply(TreeNode.scala:298)
    	at org.apache.spark.sql.catalyst.trees.TreeNode$$anonfun$5.apply(TreeNode.scala:321)
    	at org.apache.spark.sql.catalyst.trees.TreeNode.mapProductIterator(TreeNode.scala:179)
    	at org.apache.spark.sql.catalyst.trees.TreeNode.transformChildren(TreeNode.scala:319)
    	at org.apache.spark.sql.catalyst.trees.TreeNode.transformUp(TreeNode.scala:298)
    	at org.apache.spark.sql.execution.SparkPlanner$$anonfun$plan$1.apply(SparkPlanner.scala:48)
    	at org.apache.spark.sql.execution.SparkPlanner$$anonfun$plan$1.apply(SparkPlanner.scala:48)



Run the classifier on the test sets


```python
tf = model_nb.transform(testing_articles)
```

Get the prediction matrix and save it to a csv file


```python
matrix = tf.groupBy("langId", "prediction").count().collect()
total_articles = tf.groupBy("langId").count().collect()
```

Also, get the langId -> lang matches. Note that if there were empty wikis, they won't appear in `langIDs`.


```python
langIDs = sorted(set([(i[0], str(i[1])) for i in tf.select("langId", "lang").collect()]), key=lambda x: x[0])
```


```python
print(set(map(lambda e: e[1], langIDs)).symmetric_difference(set(langs)))
```

    set(['kjwiki', 'howiki', 'muswiki'])



```python
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
```


```python

```
