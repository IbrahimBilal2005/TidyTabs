import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def analyze_misclassification():
    """Analyze why certain titles are being misclassified"""
    
    # Load model components
    model = joblib.load("ml/sklearn/model.joblib")
    vectorizer = joblib.load("ml/sklearn/vectorizer.joblib")
    label_encoder = joblib.load("ml/sklearn/label_encoder.joblib")
    
    # Problematic examples
    problematic_titles = [
        "UofT Rate My Professor",
        "UofT GPA Calculator", 
        "University of Toronto Course Selection",
        "UTM Academic Calendar",
        "Ryerson University Admission Requirements"
    ]
    
    print("=== ANALYZING MISCLASSIFICATIONS ===\n")
    
    # Make predictions
    X = vectorizer.transform(problematic_titles)
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    predicted_labels = label_encoder.inverse_transform(predictions)
    
    # Show detailed analysis
    for i, title in enumerate(problematic_titles):
        predicted = predicted_labels[i]
        confidence = np.max(probabilities[i])
        
        print(f"Title: '{title}'")
        print(f"Predicted: {predicted} (confidence: {confidence:.3f})")
        print(f"Should be: Education")
        
        # Show top 3 category probabilities
        top_indices = np.argsort(probabilities[i])[-3:][::-1]
        print("Top 3 predictions:")
        for idx in top_indices:
            category = label_encoder.classes_[idx]
            prob = probabilities[i][idx]
            print(f"  {category}: {prob:.3f}")
        
        # Analyze which features triggered this prediction
        feature_weights = X[i].toarray()[0]
        non_zero_features = np.where(feature_weights > 0)[0]
        
        print("Active features (words that influenced prediction):")
        feature_names = vectorizer.get_feature_names_out()
        for feat_idx in non_zero_features:
            weight = feature_weights[feat_idx]
            word = feature_names[feat_idx]
            print(f"  '{word}': {weight:.3f}")
        
        print("-" * 60)

def create_education_rules():
    """Create rule-based overrides for obvious education cases"""
    
    education_keywords = [
        # Universities and colleges
        'university', 'college', 'uoft', 'utoronto', 'ryerson', 'york university',
        'mcmaster', 'waterloo', 'queens', 'ubc', 'mcgill', 'carleton',
        
        # Academic terms
        'course', 'gpa', 'grade', 'academic', 'semester', 'transcript',
        'enrollment', 'registration', 'tuition', 'scholarship', 'professor',
        'lecture', 'tutorial', 'exam', 'assignment', 'syllabus',
        
        # Educational platforms
        'rate my professor', 'ratemyprofessor', 'course selection',
        'degree audit', 'academic calendar', 'class schedule'
    ]
    
    return education_keywords

def enhanced_predict_categories(titles: list[str]) -> dict:
    """Enhanced prediction with rule-based overrides"""
    
    # Load model components
    try:
        model = joblib.load("ml/model.joblib")
        vectorizer = joblib.load("ml/vectorizer.joblib")
        label_encoder = joblib.load("ml/label_encoder.joblib")
    except:
        return {"Other": titles}
    
    grouped = {}
    education_keywords = create_education_rules()
    
    for title in titles:
        try:
            # First, check for education rule overrides
            title_lower = title.lower()
            is_education = False
            
            # Check for university/education keywords
            for keyword in education_keywords:
                if keyword in title_lower:
                    is_education = True
                    break
            
            if is_education:
                category = "Education"
                print(f"Rule override: '{title}' -> Education")
            else:
                # Use ML model
                X = vectorizer.transform([title])
                prediction = model.predict(X)[0]
                probability = model.predict_proba(X)[0]
                confidence = np.max(probability)
                
                if confidence < 0.05:
                    category = "Other"
                else:
                    category = label_encoder.inverse_transform([prediction])[0]
            
            # Add to grouped results
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(title)
            
        except Exception as e:
            print(f"Error processing '{title}': {e}")
            if "Other" not in grouped:
                grouped["Other"] = []
            grouped["Other"].append(title)
    
    return grouped

def improve_training_data():
    """Suggest improvements to training data"""
    
    print("=== TRAINING DATA IMPROVEMENT SUGGESTIONS ===\n")
    
    additional_education_examples = [
        {"title": "UofT Rate My Professor", "category": "Education"},
        {"title": "University of Toronto GPA Calculator", "category": "Education"},
        {"title": "Ryerson Course Selection Guide", "category": "Education"},
        {"title": "York University Academic Calendar", "category": "Education"},
        {"title": "UTM Degree Audit", "category": "Education"},
        {"title": "Waterloo Co-op Portal", "category": "Education"},
        {"title": "McGill Transcript Request", "category": "Education"},
        {"title": "UBC Student Information System", "category": "Education"},
        {"title": "Carleton University Registration", "category": "Education"},
        {"title": "OCAD University Portfolio Submission", "category": "Education"},
        
        # Add more finance examples to distinguish
        {"title": "Mortgage Rate Calculator", "category": "Finance"},
        {"title": "Investment Portfolio Tracker", "category": "Finance"},
        {"title": "Loan Payment Calculator", "category": "Finance"},
        {"title": "Tax Rate Calculator", "category": "Finance"},
        {"title": "Interest Rate Calculator", "category": "Finance"},
        
        # Add more work examples with "calculator" 
        {"title": "Salary Calculator Tool", "category": "Work"},
        {"title": "Project Time Calculator", "category": "Work"},
        {"title": "Team Performance Calculator", "category": "Work"},
    ]
    
    print("Consider adding these examples to your training data:")
    print("(This will help the model learn the difference between education and finance calculators)")
    
    for example in additional_education_examples:
        print(f"  {example}")
    
    return additional_education_examples

def test_improvements():
    """Test the enhanced prediction function"""
    
    print("\n=== TESTING ENHANCED PREDICTIONS ===\n")
    
    test_cases = [
        # Problematic cases
        "UofT Rate My Professor",
        "University of Toronto GPA Calculator", 
        "Ryerson Course Selection",
        "McGill University Transcript",
        
        # Should stay as finance
        "TD Bank Mortgage Calculator",
        "RBC Investment Calculator",
        "BMO Loan Rate Calculator",
        
        # Should stay as other categories
        "Netflix - Watch Movies",
        "Gmail - Check Email",
        "Amazon - Buy Products"
    ]
    
    print("Enhanced predictions with rules:")
    result = enhanced_predict_categories(test_cases)
    
    for category, titles in result.items():
        print(f"\n{category}:")
        for title in titles:
            print(f"  - {title}")

if __name__ == "__main__":
    # Run analysis
    analyze_misclassification()
    
    # Test improvements
    test_improvements()
    
    # Suggest training data improvements
    additional_examples = improve_training_data()
    
    print(f"\n=== SOLUTION OPTIONS ===")
    print("1. QUICK FIX: Use the enhanced_predict_categories function with education rules")
    print("2. BETTER FIX: Add the suggested examples to your training data and retrain")
    print("3. HYBRID: Use rules for obvious cases + retrain for edge cases")