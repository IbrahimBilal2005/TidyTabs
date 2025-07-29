import os
import joblib
import numpy as np

# Path to the sklearn directory
MODEL_DIR = os.path.join(os.path.dirname(__file__), "sklearn")

# Load model components once
try:
    model = joblib.load(os.path.join(MODEL_DIR, "model.joblib"))
    vectorizer = joblib.load(os.path.join(MODEL_DIR, "vectorizer.joblib"))
    label_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))
    try:
        threshold = joblib.load(os.path.join(MODEL_DIR, "threshold.joblib"))
    except:
        threshold = 0.50  # Reasonable default threshold
except Exception as e:
    model = vectorizer = label_encoder = None
    threshold = 0.50

def predict_categories(titles: list[str]) -> dict:
    """
    Predict categories for browser tab titles with optimized threshold

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

        # Group by category with dynamic threshold
        for i, (title, label) in enumerate(zip(titles, labels)):
            confidence = np.max(probabilities[i])
            final_label = label if confidence >= threshold else "Other"

            if final_label not in grouped:
                grouped[final_label] = []
            grouped[final_label].append(title)

    except Exception:
        grouped["Other"] = titles

    return grouped

def predict_categories_with_confidence(titles: list[str], custom_threshold: float = None) -> dict:
    """
    Predict categories with confidence scores

    Args:
        titles: List of tab titles to classify
        custom_threshold: Override default threshold

    Returns:
        Dictionary with categories as keys and lists of dicts as values
    """
    grouped = {}
    use_threshold = custom_threshold if custom_threshold is not None else threshold

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
            final_label = label if confidence >= use_threshold else "Other"

            if final_label not in grouped:
                grouped[final_label] = []

            grouped[final_label].append({
                "title": title,
                "confidence": float(confidence)
            })

    except Exception:
        grouped["Other"] = [{"title": title, "confidence": 0.0} for title in titles]

    return grouped
