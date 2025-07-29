import os
import joblib
import numpy as np

MODEL_DIR = os.path.dirname(__file__)

# Load model components once
try:
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.joblib"))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))
except Exception as e:
    model = vectorizer = label_encoder = None

def predict_categories(titles: list[str]) -> dict:
    """
    Predict categories for browser tab titles
    
    Args:
        titles: List of tab titles to classify
    
    Returns:
        Dictionary with categories as keys and lists of titles as values
    """
    grouped = {}
    
    if not titles or model is None:
        grouped["Other"] = titles if titles else []
        return grouped
    
    try:
        # Transform and predict
        X = vectorizer.transform(titles)
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        labels = label_encoder.inverse_transform(predictions)
        
        # Group by category with confidence threshold
        for i, (title, label) in enumerate(zip(titles, labels)):
            confidence = np.max(probabilities[i])
            
            # Use threshold of 0.3 for 200+ samples per category
            final_label = label if confidence >= 0.3 else "Other"
            
            if final_label not in grouped:
                grouped[final_label] = []
            grouped[final_label].append(title)
    
    except Exception:
        grouped["Other"] = titles
    
    return grouped

def predict_categories_with_confidence(titles: list[str], threshold: float = 0.3) -> dict:
    """
    Predict categories with confidence scores
    
    Args:
        titles: List of tab titles to classify
        threshold: Confidence threshold (default 0.3 for 200+ samples)
    
    Returns:
        Dictionary with categories as keys and lists of dicts as values
        Each dict contains 'title' and 'confidence'
    """
    grouped = {}
    
    if not titles or model is None:
        grouped["Other"] = [{"title": title, "confidence": 0.0} for title in titles]
        return grouped
    
    try:
        X = vectorizer.transform(titles)
        predictions = model.predict(X)
        probabilities = model.predict_proba(X)
        labels = label_encoder.inverse_transform(predictions)
        
        for i, (title, label) in enumerate(zip(titles, labels)):
            confidence = np.max(probabilities[i])
            final_label = label if confidence >= threshold else "Other"
            
            if final_label not in grouped:
                grouped[final_label] = []
            
            grouped[final_label].append({
                "title": title,
                "confidence": float(confidence)
            })
    
    except Exception:
        grouped["Other"] = [{"title": title, "confidence": 0.0} for title in titles]
    
    return grouped 