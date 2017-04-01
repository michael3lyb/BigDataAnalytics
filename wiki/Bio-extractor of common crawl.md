# Bio-extractor of common crawl 
Based on Felix’s code, I change it to be a bio-article classifier. 
## Prepare training data
1.	Using PubMed document as positive training data. Here I use the sample data of PubMed for demo. These data just contain abstract of the article, but enough for simple classification.
 2.Using non-biology related database as negative training data. Here for demo, I just borrow the data which Felix used in english part of lorelei project. 
 3.These training data show as different articles, which I can manually label with 1(bio-related) or 0(non-bio-related)
 4.In spark, load all these datasets into DataFrame format which suitable for feature extraction and machine learning algorithm.

## Feature extraction
1.	Use Tokenizer separate the article into bag of words.
 2.Use build in TF-IDF algorithm, to calculate TF and IDF respectively, than simply multiply to get TF-IDF
 3.This will give us features of the article which can best distinguish from the others.

## Machine learning classifier
1.	For binary classification, Logistic Regression, Naïve Bayes, Random Forest can be used in MLlib pipline.
2.	Naïve Bayes performs good here, but theoretically most other classifier can beat Naïve Bayes in most scenario. We can change to other more complex algorithm if necessary.
 2.Build pipline combine feature extraction and ML training
 3.Get the classification model, which can be used for common crawl data classification.

## Result 
I test it with five example, the biology example comes from one PubMed article which not included in the training data. Non-biology example are normal sentence. The all give right result based on the classifier.

## Other issues:
Our final goal of bio-project is to build a search engine on extracted data, which can give domain specific result asked by user. For example, if user search “vitamin A”, we can give suggestion of which domain the user want to know about vitamin A, like illness(what kind of illness related with vitamin A); metabolism(how human absorb, excrete vitamin A) and so on. 
Do we need to classify articles into these domain in ETL phase(build a multiclass classifier for the extraction from common crawl), or first use a binary classifier to extract whole medical article from common crawl, than classify into different domain?