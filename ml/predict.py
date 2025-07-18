# backend/ml/predict.py

import torch
import joblib
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

# Load model and tokenizer
MODEL_PATH = "ml/distilbert_tab_classifier"
ENCODER_PATH = "ml/label_encoder.joblib"

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
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
