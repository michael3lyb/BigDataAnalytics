import re
import os, sys
from pyspark.sql import SparkSession
from pyspark import keyword_only
from pyspark.ml import Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol
from pyspark.sql.functions import udf
from pyspark.sql.types import ArrayType, StringType
from pyspark.sql.types import StructType, StructField, DoubleType, StringType

from pyspark.ml.feature import CountVectorizer, Tokenizer
from pyspark.ml.feature import HashingTF, IDF
from pyspark.ml.classification import NaiveBayes
from pyspark.ml import Pipeline
from pyspark.ml.classification import OneVsRest
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

spark = SparkSession.builder.getOrCreate()
begin_re = re.compile("^====")

def is_text(line):
    line = line.strip()
    if not line or begin_re.match(line):
        return False
    return True

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

schema = StructType([
    StructField("fullText", StringType(), True), StructField("category", DoubleType(), False)
])

def load_article(category_name, category_id):
    text_file = spark.sparkContext.textFile("{}/*".format(category_name))
    return text_file.filter(is_text).map(lambda l: (l, float(category_id))).toDF(schema)

micro_articles = load_article("microbiol-small", 0)
cancer_articles = load_article("cancer-small", 1)
otherMed_articles = load_article("others-small", 2)

bio = micro_articles.unionAll(cancer_articles)
inputData = bio.unionAll(otherMed_articles)
(train, test) = inputData.randomSplit([0.8, 0.2])

os.environ['PYTHONPATH'] = ':'.join(sys.path)

punctuation_stripper = PunctuationStripper(inputCol="fullText", outputCol="strippedText")
tokenizer = Tokenizer(inputCol="strippedText", outputCol="words")
# CountVectorizer and HashingTF both can be used to get term frequency vectors
# cv = CountVectorizer(inputCol="words", outputCol="rawFeatures")
hashingTF = HashingTF(inputCol="words", outputCol="rawFeatures")
idf = IDF(inputCol="rawFeatures", outputCol="features")

nb = NaiveBayes(featuresCol="features", labelCol="category", modelType="multinomial")
# instantiate the One Vs Rest Classifier.
ovr = OneVsRest(classifier=nb, labelCol="category")

pipeline = Pipeline(stages=[punctuation_stripper, tokenizer, hashingTF, idf, ovr])

ovrModel = pipeline.fit(train)

predictions = ovrModel.transform(test)

evaluator = MulticlassClassificationEvaluator(metricName="accuracy", labelCol="category")
# compute the classification error on test data.
accuracy = evaluator.evaluate(predictions)
print("Test Error : " + str(1 - accuracy))

tf = spark.createDataFrame([("Bactibilia has several consequences to human health", ),
                            ("Assessing the bile microbiology of patients with biliopancreatic diseases in order to identify bacteria and their possible infectious complications", ),
                            ("Thirty bile samples from patients at mean age ≈57.7 years, mostly female (n=18), were assessed. ", ),
                            ("Julius Caesar was a Roman general", ),
                            ("big data analysis is great", ),
                            ("do you know snow crash", ),
                           ], ["fullText"])
tf = ovrModel.transform(tf)
tf.select(tf['fullText'], tf['prediction']).show()