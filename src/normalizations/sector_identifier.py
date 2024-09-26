import os
import pandas as pd
import nltk
import gensim
from gensim.utils import simple_preprocess
from gensim.parsing.preprocessing import STOPWORDS
from nltk.stem.porter import *
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
import joblib

class SectorID:
    # Update the path to point to the correct location of jobDS.csv
    data_path = os.path.join(os.path.dirname(__file__), '../data/jobDS.csv')  
    model_path = os.path.join(os.path.dirname(__file__), 'saved_sgd_model.joblib')  # Model path
    columnOne = "Job Title"
    columnTwo = "Sector"
    
    # Check if the CSV file exists
    if not os.path.exists(data_path):
        print(f"Error: The file {data_path} does not exist.")
        exit(1)
    
    dataFrame = pd.read_csv(data_path)
    X_train, X_test, y_train, y_test, weights = [None, None, None, None, None]

    @classmethod
    def cleanData(cls):
        cleanedFrame = cls.dataFrame.drop_duplicates(subset=cls.columnOne)
        return cleanedFrame.dropna(subset=[cls.columnOne])
  
    @classmethod
    def textToLowerCase(cls, text):
        result = ""
        for token in simple_preprocess(text):
            if token not in STOPWORDS and len(token) >= 2:
                token = token.lower()  # lowercase text
                result += token + " "  # append to result
        return result.strip()

    @classmethod
    def cleaner(cls):
        return cls.cleanData().map(cls.textToLowerCase)
  
    @classmethod
    def splitData(cls):
        cf = cls.cleaner()
        x = cf[cls.columnOne]
        y = cf[cls.columnTwo]
        cls.X_train, cls.X_test, cls.y_train, cls.y_test = train_test_split(x, y, test_size=0.25, random_state=42)
        cls.weights = compute_sample_weight("balanced", cls.y_train)
  
    @classmethod
    def createModel(cls):
        return Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, random_state=42, max_iter=9999, tol=None)),
        ])

    @classmethod
    def trainModel(cls, model):
        cls.splitData()
        model.fit(cls.X_train, cls.y_train, **{'clf__sample_weight': cls.weights})
        y_pred = model.predict(cls.X_test)
        cls.saveModel(model)
        print('accuracy %s' % accuracy_score(y_pred, cls.y_test))

    @classmethod
    def saveModel(cls, model):
        # Use the defined model path to save the model
        joblib.dump(model, cls.model_path)
        print(f"Model saved to {cls.model_path}")

    @classmethod
    def findSector(cls, jobTitle):
        # Ensure the model exists before loading
        if not os.path.exists(cls.model_path):
            print(f"Error: Model file {cls.model_path} does not exist. Please train the model first.")
            exit(1)
        pipeline_loaded = joblib.load(cls.model_path)
        prediction = pipeline_loaded.predict([jobTitle])
        return prediction[0]
  
# Uncomment the following line of code to train and save a new model
# SectorID.trainModel(SectorID.createModel())
