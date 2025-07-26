#/ml/predict.py

import os
import torch
import joblib
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

MODEL_PATH = os.path.join(os.path.dirname(__file__), "distilbert_tab_classifier")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "label_encoder.joblib")

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH, local_files_only=True)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True)

model.eval()

label_encoder = joblib.load(ENCODER_PATH)

def predict_categories(titles: list[str]) -> dict:
    inputs = tokenizer(titles, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)
        predicted_indices = torch.argmax(outputs.logits, dim=1).tolist()
        predicted_labels = label_encoder.inverse_transform(predicted_indices)

    # Group tab titles by predicted category
    grouped = {}
    for title, label in zip(titles, predicted_labels):
        grouped.setdefault(label, []).append(title)
    return grouped