#/ml/predict.py

import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import ComplementNB
from sklearn.preprocessing import LabelEncoder
import joblib

def predict_categories(titles: list[str]):

    # Load the saved model and label encoder
    clf = joblib.load("ml/data/tab_classifier.pkl")
    label_encoder = joblib.load("ml/data/label_encoder.pkl")

    # Predict
    predictions = clf.predict(titles)

    # Convert numeric labels back to category names
    decoded_preds = label_encoder.inverse_transform(predictions)

    # Map each category to a list of matching titles
    predictions = {}

    for title, category in zip(titles, decoded_preds):
        try:
            predictions[category].append(title)
        
        except Exception as e:
            predictions[category] = [title]
        
    return predictions
