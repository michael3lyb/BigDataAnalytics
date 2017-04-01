
# coding: utf-8

# # PubMed microbiology and cancer classifier
# 
# 

# Create the spark session

# In[1]:

from pyspark.sql import SparkSession

spark = SparkSession\
    .builder\
    .appName("microbiolCancer")\
    .config("spark.driver.maxResultSize", "0")\
    .getOrCreate()


# Filter to remove empty lines and file structure

# In[2]:

import re

begin_re = re.compile("^====")

def is_text(line):
    line = line.strip()
    if not line or begin_re.match(line):
        return False
    
    return True


# In[3]:

from pyspark import keyword_only
from pyspark.ml import Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, StringType

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


# load PubMed and non-PubMed articles in to dataframe

# In[4]:

from pyspark.sql.types import StructType, StructField, DoubleType, StringType
schema = StructType([
    StructField("fullText", StringType(), True), StructField("category", DoubleType(), False)
])

def load_article(category_name, category_id):
    text_file = spark.sparkContext.textFile("{}.txt".format(category_name))
    return text_file.filter(is_text).map(lambda l: (l, float(category_id))).toDF(schema)


# The loading and preprocessing should be turned into Spark tasks.

# In[5]:

micro_articles = load_article("microbiol", 0)
cancer_articles = load_article("cancer", 1)
otherMed_articles = load_article("other", 2)


# In[8]:

bio = micro_articles.unionAll(cancer_articles)
inputData = bio.unionAll(otherMed_articles)
(train, test) = inputData.randomSplit([0.8, 0.2])


# The following is a workaround for pyspark not finding numpy, [taken from the GitHub issue](https://github.com/jupyter/docker-stacks/issues/109).

# In[9]:

import os, sys

os.environ['PYTHONPATH'] = ':'.join(sys.path)


# delete TFIDF add ngram

# In[10]:

# from pyspark.ml.feature import HashingTF, IDF
from pyspark.ml.feature import CountVectorizer, Tokenizer, StringIndexer, NGram, VectorAssembler

from pyspark.ml.classification import NaiveBayes
from pyspark.ml import Pipeline
from pyspark.ml.classification import OneVsRest
from pyspark.ml.evaluation import MulticlassClassificationEvaluator


punctuation_stripper = PunctuationStripper(inputCol="fullText", outputCol="strippedText")
tokenizer = Tokenizer(inputCol="strippedText", outputCol="words")
# CountVectorizer and HashingTF both can be used to get term frequency vectors
# cv = CountVectorizer(inputCol="words", outputCol="rawFeatures")

# hashingTF = HashingTF(inputCol="words", outputCol="rawFeatures")
# idf = IDF(inputCol="rawFeatures", outputCol="features")

threeGram = NGram(n=3, inputCol="words", outputCol="threeGrams")
fourGram = NGram(n=4, inputCol="words", outputCol="fourGrams")
cv_3g = CountVectorizer(inputCol="threeGrams", outputCol="threeGramsCountVector")
cv_4g = CountVectorizer(inputCol="fourGrams", outputCol="fourGramsCountVector")
fc = VectorAssembler(inputCols=["threeGramsCountVector", "fourGramsCountVector"], outputCol="ngramsCountVector")

nb = NaiveBayes(featuresCol="ngramsCountVector", labelCol="category", modelType="multinomial")
# instantiate the One Vs Rest Classifier.
ovr = OneVsRest(classifier=nb, labelCol="category")


# TF -> IDF -> NaiveBayes

# In[11]:

pipeline = Pipeline(stages=[punctuation_stripper,tokenizer, threeGram, fourGram, cv_3g, cv_4g, fc, nb])


# In[12]:

ovrModel = pipeline.fit(train)


# score the model on test data

# In[13]:

predictions = ovrModel.transform(test)
micro_articles_count = test.filter(test['category'] == 0.0).count()
print("micro_articles number:")
print(micro_articles_count)
cancer_articles_count = test.filter(test['category'] == 1.0).count()
print("cancer_articles number:")
print(cancer_articles_count)
otherMed_articles_count = test.filter(test['category'] == 2.0).count()
print("otherMed_articles number:")
print(otherMed_articles_count)


# obtain evaluator.

# In[15]:

evaluator = MulticlassClassificationEvaluator(metricName="accuracy", labelCol="category")
# compute the classification error on test data.
accuracy = evaluator.evaluate(predictions)
print("Test Error : " + str(1 - accuracy))


# In[16]:

#  confusion matrix
from pyspark.mllib.evaluation import MulticlassMetrics
predictionsAndLabelsNB = predictions.select("prediction", "category")


# In[18]:

metricsNB = MulticlassMetrics(predictionsAndLabelsNB.rdd)

accuracyNB2 = metricsNB.accuracy
print("Naive Bayes accuracy:")
print(accuracyNB2)

confusionMatrixNB = metricsNB.confusionMatrix().toArray()
print("Confusion Matrix: ")
print(confusionMatrixNB)


# Try classifying a few basic sentences.

# In[15]:

tf = spark.createDataFrame([("Bactibilia has several consequences to human health", ),
                            ("Assessing the bile microbiology of patients with biliopancreatic diseases in order to identify bacteria and their possible infectious complications", ),
                            ("Thirty bile samples from patients at mean age ≈57.7 years, mostly female (n=18), were assessed. ", ),
                            ("Julius Caesar was a Roman general", ),
                            ("big data analysis is great", ),
                            ("do you know snow crash", ),
                           ], ["fullText"])
tf = ovrModel.transform(tf)
tf.select(tf['fullText'], tf['prediction']).show()

