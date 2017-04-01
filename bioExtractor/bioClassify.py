from __future__ import print_function

import sys
from random import random
from operator import add

from pyspark.sql import SparkSession

import re

from pyspark import keyword_only
from pyspark.ml import Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, StringType

from pyspark.sql.types import StructType, StructField, DoubleType, StringType
import os, sys

from pyspark.ml.feature import CountVectorizer, Tokenizer
from pyspark.ml.feature import HashingTF, IDF
from pyspark.ml.classification import NaiveBayes
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.mllib.evaluation import MulticlassMetrics

class PunctuationStripper(Transformer, HasInputCol, HasOutputCol):
    
    @keyword_only
    def __init__(self, inputCol=None, outputCol=None):
        super(PunctuationStripper, self).__init__()
        kwargs = self.__init__._input_kwargs
        self.setParams(**kwargs)

    @keyword_only
    def setParams(self, inputCol=None, outputCol=None):
        kwargs = self.setParams._input_kwargs
        return self._set(**kwargs)

    def _transform(self, dataset):
        punct_re = re.compile(r'[^\w\s]', re.UNICODE)
        
        def strip(s):
            return punct_re.sub('', s)
        
        out_col = self.getOutputCol()
        in_col = dataset[self.getInputCol()]
        mapper = udf(strip, StringType())
        
        return dataset.withColumn(out_col, mapper(in_col))



if __name__ == "__main__":
    """
        Usage: 
    """
    spark = SparkSession\
        .builder\
        .appName("bioClassify")\
        .config("spark.driver.maxResultSize", "0")\
        .getOrCreate()

    begin_re_wiki = re.compile("<doc.*>$")
    end_re_wiki = re.compile("^</doc>$")
    def is_text_wiki(line):
        line = line.strip()
        if not line or begin_re_wiki.match(line) or end_re_wiki.match(line):
            return False
        
        return True 
        
    begin_re_pubmed = re.compile("^====")

    def is_text_pubmed(line):
        line = line.strip()
        if not line or begin_re_pubmed.match(line):
            return False
        
        return True

    
    schema = StructType([
        StructField("fullText", StringType(), True), StructField("category", DoubleType(), False)
    ])

    def load_article_wiki(category_name, category_id):
        text_file = spark.sparkContext.textFile("{}/*".format(category_name))
        return text_file.filter(is_text_wiki).map(lambda l: (l, float(category_id))).toDF(schema)

    def load_article_pubmed(category_name, category_id):
        text_file = spark.sparkContext.textFile("{}/*".format(category_name))
        return text_file.filter(is_text_wiki).map(lambda l: (l, float(category_id))).toDF(schema)

    bio_articles = load_article_pubmed("pubmed-AF-combine", 0)
    other_articles = load_article_wiki("enwiki", 1)
    
    # bio_articles.show()   
    df = bio_articles.unionAll(other_articles)
    (train, test) = df.randomSplit([0.8, 0.2])

    os.environ['PYTHONPATH'] = ':'.join(sys.path)

    punctuation_stripper = PunctuationStripper(inputCol="fullText", outputCol="strippedText")
    tokenizer = Tokenizer(inputCol="strippedText", outputCol="words")
    # CountVectorizer and HashingTF both can be used to get term frequency vectors
    # cv = CountVectorizer(inputCol="words", outputCol="rawFeatures")

    hashingTF = HashingTF(inputCol="words", outputCol="rawFeatures")
    idf = IDF(inputCol="rawFeatures", outputCol="features")

    nb = NaiveBayes(featuresCol="features", labelCol="category", modelType="multinomial")

    pipeline = Pipeline(stages=[punctuation_stripper, tokenizer, hashingTF, idf, nb])    

    model = pipeline.fit(train)

    predictions = model.transform(test)
    other_articles_count = test.filter(test['category'] == 1.0).count()
    print("other_articles number:")
    print(other_articles_count)
    bio_articles_count = test.filter(test['category'] == 0.0).count()
    print("bio_articles number:")
    print(bio_articles_count)

    evaluator = MulticlassClassificationEvaluator(metricName="accuracy", labelCol="category")
    # compute the classification error on test data.
    accuracy = evaluator.evaluate(predictions)
    print("Test Error : " + str(1 - accuracy))

    # confusion matrix
    
    predictionsAndLabelsNB = predictions.select("prediction", "category")
    metricsNB = MulticlassMetrics(predictionsAndLabelsNB.rdd)

    accuracyNB2 = metricsNB.accuracy
    print("Naive Bayes accuracy:")
    print(accuracyNB2)

    confusionMatrixNB = metricsNB.confusionMatrix().toArray()
    print("Confusion Matrix: ")
    print(confusionMatrixNB)
    
    tf = spark.createDataFrame([("Bactibilia has several consequences to human health", ),
                                ("Assessing the bile microbiology of patients with biliopancreatic diseases in order to identify bacteria and their possible infectious complications", ),
                                ("Thirty bile samples from patients at mean age 57.7 years, mostly female (n=18), were assessed. ", ),
                                ("Julius Caesar was a Roman general", ),
                                ("big data analysis is great", ),
                                ("do you know snow crash", ),
                               ], ["fullText"])
    tf = model.transform(tf)
    tf.select(tf['fullText'], tf['prediction']).show()    

    spark.stop()