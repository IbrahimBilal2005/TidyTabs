import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import os

def load_and_prepare_data(file_path="ml/data/training_data_realistic.json"):
    """Load training data from JSON file"""
    with open(file_path) as f:
        data = json.load(f)
        
    titles = [item["title"] for item in data]
    categories = [item["category"] for item in data]
    
    return titles, categories

def create_vectorizer():
    """Create TF-IDF vectorizer optimized for tab titles"""
    return TfidfVectorizer(
        max_features=1500,  # Reduced for shorter tab titles
        ngram_range=(1, 3),  # Include trigrams for better context
        lowercase=True,
        min_df=1,  # Don't eliminate single occurrences - important for domains
        max_df=0.85,  # Slightly more restrictive
        stop_words='english',
        strip_accents='ascii',
        # Add character-level features for URLs/domains
        analyzer='word',
        token_pattern=r'\b\w+\b',
        sublinear_tf=True  # Better for short documents
    )

def train_models(X, y):
    """Train multiple models with proper validation"""
    # Create train/val/test splits
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp  # ~15% of total
    )
    
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=2000,
            C=2.0,  # Slightly more regularization
            solver='saga',
            random_state=42,
            class_weight='balanced'
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=150,
            max_depth=15,
            min_samples_split=5,  # Prevent overfitting
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        ),
        'SVM': SVC(
            kernel='linear',
            C=1.5,
            random_state=42,
            probability=True,
            class_weight='balanced'
        )
    }
    
    # Model selection using validation set
    best_model = None
    best_score = 0
    best_name = ""
    
    print("Model validation scores:")
    for name, model in models.items():
        model.fit(X_train, y_train)
        val_predictions = model.predict(X_val)
        val_accuracy = accuracy_score(y_val, val_predictions)
        print(f"{name}: {val_accuracy:.3f}")
        
        if val_accuracy > best_score:
            best_score = val_accuracy
            best_model = model
            best_name = name
    
    # Final test evaluation
    test_predictions = best_model.predict(X_test)
    test_accuracy = accuracy_score(y_test, test_predictions)
    
    print(f"\nBest model: {best_name}")
    print(f"Validation accuracy: {best_score:.3f}")
    print(f"Test accuracy: {test_accuracy:.3f}")
    
    return best_model

def calculate_optimal_threshold(model, vectorizer, label_encoder, titles, categories):
    """Calculate optimal confidence threshold using validation data"""
    # Use a small validation set to find optimal threshold
    X_val = vectorizer.transform(titles[-300:])  # Last 300 samples for better estimates
    y_val = label_encoder.transform(categories[-300:])
    
    probabilities = model.predict_proba(X_val)
    max_probs = np.max(probabilities, axis=1)
    predictions = model.predict(X_val)
    
    # Test different thresholds with focus on higher values
    thresholds = np.arange(0.4, 0.85, 0.05)
    best_threshold = 0.5
    best_score = 0
    
    print("\nThreshold Analysis:")
    print("Threshold | Accuracy | Coverage | Score")
    print("-" * 40)
    
    for threshold in thresholds:
        # Apply threshold - if below threshold, classify as "Other"
        confident_mask = max_probs >= threshold
        
        if np.sum(confident_mask) > 10:  # Need at least 10 confident predictions
            confident_accuracy = accuracy_score(
                y_val[confident_mask], 
                predictions[confident_mask]
            )
            coverage = np.mean(confident_mask)
            
            # Prioritize accuracy over coverage for better organization
            # Weight accuracy more heavily (70/30 split)
            score = (0.7 * confident_accuracy) + (0.3 * coverage)
            
            print(f"{threshold:.2f}      | {confident_accuracy:.3f}    | {coverage:.3f}    | {score:.3f}")
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
    
    print(f"\nSelected threshold: {best_threshold:.2f}")
    return best_threshold

def save_model_components(model, vectorizer, label_encoder, threshold=0.5):
    """Save model components to files"""
    os.makedirs("ml", exist_ok=True)
    
    joblib.dump(model, "ml/model.joblib")
    joblib.dump(vectorizer, "ml/vectorizer.joblib")
    joblib.dump(label_encoder, "ml/label_encoder.joblib")
    joblib.dump(threshold, "ml/threshold.joblib")

def main():
    """Main training pipeline"""
    # Load data
    titles, categories = load_and_prepare_data()
    print(f"Loaded {len(titles)} samples across {len(set(categories))} categories")
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(categories)
    
    # Create features
    vectorizer = create_vectorizer()
    X = vectorizer.fit_transform(titles)
    
    # Train model
    best_model = train_models(X, y)
    
    # Find optimal threshold
    optimal_threshold = calculate_optimal_threshold(
        best_model, vectorizer, label_encoder, titles, categories
    )
    
    # Save everything
    save_model_components(best_model, vectorizer, label_encoder, optimal_threshold)
    print("Model saved successfully")

if __name__ == "__main__":
    main()


# Updated prediction module
import os
import joblib
import numpy as np

MODEL_DIR = os.path.dirname(__file__)

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
            
            # Use learned optimal threshold
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
