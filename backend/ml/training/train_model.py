import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import os
from collections import Counter

def load_and_prepare_data(file_path="ml/data/training_data_realistic.json"):
    """Load training data from JSON file with data quality checks"""
    with open(file_path) as f:
        data = json.load(f)
        
    titles = [item["title"] for item in data]
    categories = [item["category"] for item in data]
    
    # Print dataset statistics
    print(f"Dataset size: {len(titles)} samples")
    category_counts = Counter(categories)
    print(f"Categories ({len(category_counts)}): {dict(category_counts)}")
    
    # Check for class imbalance
    min_samples = min(category_counts.values())
    max_samples = max(category_counts.values())
    imbalance_ratio = max_samples / min_samples
    print(f"Class imbalance ratio: {imbalance_ratio:.2f}")
    
    if imbalance_ratio > 10:
        print("WARNING: High class imbalance detected. Consider adding more samples to underrepresented classes.")
    
    return titles, categories

def create_vectorizer(dataset_size):
    """Create TF-IDF vectorizer that scales with dataset size"""
    # Scale max_features with dataset size but cap it
    base_features = min(2000, max(1500, dataset_size // 10))
    
    return TfidfVectorizer(
        max_features=base_features,
        ngram_range=(1, 3),  # Keep trigrams for context
        lowercase=True,
        min_df=max(1, dataset_size // 1000),  # Scale min_df with dataset size
        max_df=0.85,
        stop_words='english',
        strip_accents='ascii',
        analyzer='word',
        token_pattern=r'\b\w+\b',
        sublinear_tf=True
    )

def train_models(X, y, dataset_size):
    """Train multiple models with parameters scaled to dataset size"""
    # Adjust test size based on dataset size
    test_size = max(0.1, min(0.2, 200 / dataset_size))  # Between 10-20%, min 200 samples
    
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    
    val_size = test_size / (1 - test_size)  # Keep validation size proportional
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_size, random_state=42, stratify=y_temp
    )
    
    print(f"Split sizes - Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")
    
    # Scale model parameters with dataset size
    rf_estimators = min(200, max(100, dataset_size // 20))
    rf_max_depth = min(20, max(10, dataset_size // 100))
    
    models = {
        'Logistic Regression': LogisticRegression(
            max_iter=3000,  # Increased for larger datasets
            C=1.0,  # Start with less regularization for larger datasets
            solver='saga',
            random_state=42,
            class_weight='balanced',
            n_jobs=-1  # Use all cores
        ),
        'Random Forest': RandomForestClassifier(
            n_estimators=rf_estimators,
            max_depth=rf_max_depth,
            min_samples_split=max(2, dataset_size // 1000),  # Scale with dataset
            min_samples_leaf=max(1, dataset_size // 2000),
            random_state=42,
            class_weight='balanced',
            n_jobs=-1  # Use all cores
        ),
        'SVM': SVC(
            kernel='linear',
            C=1.0,  # Adjust C based on dataset size
            random_state=42,
            probability=True,
            class_weight='balanced'
        )
    }
    
    # Use cross-validation for more robust model selection with larger datasets
    if dataset_size > 1000:
        print("Using cross-validation for model selection...")
        cv_scores = {}
        
        for name, model in models.items():
            # Use stratified k-fold with appropriate k
            k_folds = min(10, max(3, dataset_size // 200))
            cv = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=42)
            
            scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='accuracy', n_jobs=-1)
            cv_scores[name] = scores.mean()
            print(f"{name}: {scores.mean():.3f} (±{scores.std():.3f})")
        
        # Select best model and train on full training set
        best_name = max(cv_scores, key=cv_scores.get)
        best_model = models[best_name]
        best_model.fit(X_train, y_train)
        
    else:
        # Use validation set for smaller datasets
        print("Using validation set for model selection...")
        best_model = None
        best_score = 0
        best_name = ""
        
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
    print(f"Test accuracy: {test_accuracy:.3f}")
    
    # Print detailed classification report
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, test_predictions))
    
    return best_model

def calculate_optimal_threshold(model, vectorizer, label_encoder, titles, categories):
    """Calculate optimal confidence threshold with improved methodology"""
    # Use more samples for threshold calculation if available
    validation_size = min(500, max(100, len(titles) // 5))
    
    X_val = vectorizer.transform(titles[-validation_size:])
    y_val = label_encoder.transform(categories[-validation_size:])
    
    probabilities = model.predict_proba(X_val)
    max_probs = np.max(probabilities, axis=1)
    predictions = model.predict(X_val)
    
    # More granular threshold testing
    thresholds = np.arange(0.20, 0.42, 0.02) 
    best_threshold = 0.5
    best_score = 0
    
    print("\nThreshold Analysis (showing top candidates):")
    print("Threshold | Accuracy | Coverage | Score")
    print("-" * 40)
    
    threshold_scores = []
    
    for threshold in thresholds:
        confident_mask = max_probs >= threshold
        
        if np.sum(confident_mask) > max(5, validation_size // 20):  # At least 5% of validation
            confident_accuracy = accuracy_score(
                y_val[confident_mask], 
                predictions[confident_mask]
            )
            coverage = np.mean(confident_mask)
            
            # Balanced scoring: accuracy is important but so is coverage
            score = (0.65 * confident_accuracy) + (0.35 * coverage)
            
            threshold_scores.append((threshold, confident_accuracy, coverage, score))
            
            if score > best_score:
                best_score = score
                best_threshold = threshold
    
    # Show top 5 thresholds
    threshold_scores.sort(key=lambda x: x[3], reverse=True)
    for threshold, acc, cov, score in threshold_scores[:5]:
        print(f"{threshold:.2f}      | {acc:.3f}    | {cov:.3f}    | {score:.3f}")
    
    print(f"\nSelected threshold: {best_threshold:.2f}")
    return best_threshold

def save_model_components(model, vectorizer, label_encoder, threshold=0.5, metadata=None):
    """Save model components with metadata"""
    output_dir = "ml/sklearn"
    os.makedirs(output_dir, exist_ok=True)

    joblib.dump(model, os.path.join(output_dir, "model.joblib"))
    joblib.dump(vectorizer, os.path.join(output_dir, "vectorizer.joblib"))
    joblib.dump(label_encoder, os.path.join(output_dir, "label_encoder.joblib"))
    joblib.dump(threshold, os.path.join(output_dir, "threshold.joblib"))
    
    # Save training metadata
    if metadata:
        with open(os.path.join(output_dir, "training_metadata.json"), 'w') as f:
            json.dump(metadata, f, indent=2)

def main():
    """Main training pipeline with enhanced monitoring"""
    # Load data
    titles, categories = load_and_prepare_data()
    dataset_size = len(titles)
    
    # Encode labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(categories)
    
    # Create features
    vectorizer = create_vectorizer(dataset_size)
    X = vectorizer.fit_transform(titles)
    
    print(f"Feature matrix shape: {X.shape}")
    
    # Train model
    best_model = train_models(X, y, dataset_size)
    
    # Find optimal threshold
    optimal_threshold = calculate_optimal_threshold(
        best_model, vectorizer, label_encoder, titles, categories
    )
    
    # Prepare metadata
    metadata = {
        "training_samples": dataset_size,
        "num_categories": len(set(categories)),
        "feature_count": X.shape[1],
        "model_type": type(best_model).__name__,
        "threshold": float(optimal_threshold),
        "categories": list(label_encoder.classes_)
    }
    
    # Save everything
    save_model_components(best_model, vectorizer, label_encoder, optimal_threshold, metadata)
    print("Model saved successfully with metadata")
    
    # Final recommendations
    print("\nTraining Complete!")
    print("Recommendations for continued improvement:")
    print("1. Monitor misclassified examples and add them to training data")
    print("2. If you notice consistent patterns in 'Other' category, consider creating new categories")
    print("3. Retrain periodically as you add more data")
    if dataset_size < 1000:
        print("4. Consider collecting more training data - aim for 100+ examples per category")

if __name__ == "__main__":
    main() 