import os
import joblib
import numpy as np
import onnxruntime as ort

def debug_onnx_model():
    """Debug the ONNX model to see what's going wrong"""
    
    print("=== ONNX Model Debug ===")
    
    # Check if files exist
    print("\n1. Checking file existence:")
    files_to_check = [
        "ml/onnx/model.onnx",
        "ml/onnx/label_encoder.joblib", 
        "ml/onnx/threshold.joblib"
    ]
    
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        print(f"  {file_path}: {'✅' if exists else '❌'}")
        if exists:
            size = os.path.getsize(file_path)
            print(f"    Size: {size:,} bytes")
    
    # Try to load ONNX model
    print("\n2. Loading ONNX model:")
    try:
        sess = ort.InferenceSession("ml/onnx/model.onnx", providers=['CPUExecutionProvider'])
        print("  ✅ ONNX model loaded successfully")
        
        # Get model info
        inputs = sess.get_inputs()
        outputs = sess.get_outputs()
        print(f"  Input: {inputs[0].name} - {inputs[0].type} - {inputs[0].shape}")
        print(f"  Outputs: {len(outputs)} outputs")
        for i, output in enumerate(outputs):
            print(f"    Output {i}: {output.name} - {output.type} - {output.shape}")
            
    except Exception as e:
        print(f"  ❌ Failed to load ONNX model: {e}")
        return False
    
    # Load supporting files
    print("\n3. Loading supporting files:")
    try:
        label_encoder = joblib.load("ml/onnx/label_encoder.joblib")
        print(f"  ✅ Label encoder loaded - {len(label_encoder.classes_)} classes")
        print(f"  Classes: {list(label_encoder.classes_)}")
        
        threshold = joblib.load("ml/onnx/threshold.joblib")
        print(f"  ✅ Threshold loaded: {threshold} (type: {type(threshold)})")
        
    except Exception as e:
        print(f"  ❌ Failed to load supporting files: {e}")
        return False
    
    # Test prediction with sample data
    print("\n4. Testing predictions:")
    test_titles = [
        "GitHub - Microsoft/vscode",
        "Gmail - Inbox", 
        "Netflix - Watch Movies",
        "Stack Overflow - Python help",
        "Amazon - Shopping Cart"
    ]
    
    try:
        input_name = sess.get_inputs()[0].name
        input_data = np.array(test_titles, dtype=object)
        
        print(f"  Input data shape: {input_data.shape}")
        print(f"  Input data type: {input_data.dtype}")
        
        # Run inference
        result = sess.run(None, {input_name: input_data})
        
        print(f"  ✅ Inference successful")
        print(f"  Result types: {[type(r) for r in result]}")
        print(f"  Result shapes: {[r.shape if hasattr(r, 'shape') else len(r) for r in result]}")
        
        predictions = result[0]
        probabilities = result[1] 
        
        # Analyze results in detail
        print("\n  Detailed Results:")
        labels = label_encoder.inverse_transform(predictions)
        
        for i, title in enumerate(test_titles):
            pred_class = predictions[i]
            pred_label = labels[i]
            prob_row = probabilities[i]
            
            if isinstance(prob_row, np.ndarray):
                max_confidence = float(np.max(prob_row))
                all_probs = prob_row
            else:
                max_confidence = float(prob_row) if isinstance(prob_row, (int, float)) else 0.0
                all_probs = [prob_row]
            
            final_label = pred_label if max_confidence >= threshold else "Other"
            
            print(f"\n    Title: {title}")
            print(f"    Predicted class ID: {pred_class}")
            print(f"    Predicted label: {pred_label}")
            print(f"    Max confidence: {max_confidence:.4f}")
            print(f"    All probabilities: {all_probs}")
            print(f"    Threshold: {threshold}")
            print(f"    Final category: {final_label}")
            print(f"    Above threshold? {'✅' if max_confidence >= threshold else '❌'}")
        
    except Exception as e:
        print(f"  ❌ Prediction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Compare with original scikit-learn model
    print("\n5. Comparing with original scikit-learn model:")
    try:
        sklearn_model = joblib.load("ml/model.joblib")
        sklearn_vectorizer = joblib.load("ml/vectorizer.joblib")
        sklearn_label_encoder = joblib.load("ml/label_encoder.joblib")
        sklearn_threshold = joblib.load("ml/threshold.joblib")
        
        # Make predictions with sklearn model
        X = sklearn_vectorizer.transform(test_titles)
        sklearn_predictions = sklearn_model.predict(X)
        sklearn_probabilities = sklearn_model.predict_proba(X)
        sklearn_labels = sklearn_label_encoder.inverse_transform(sklearn_predictions)
        
        print("  Sklearn vs ONNX comparison:")
        for i, title in enumerate(test_titles):
            sklearn_conf = float(np.max(sklearn_probabilities[i]))
            sklearn_final = sklearn_labels[i] if sklearn_conf >= sklearn_threshold else "Other"
            
            onnx_conf = float(np.max(probabilities[i])) if isinstance(probabilities[i], np.ndarray) else float(probabilities[i])
            onnx_final = labels[i] if onnx_conf >= threshold else "Other"
            
            match = "✅" if sklearn_final == onnx_final else "❌"
            print(f"    {title[:30]:30} | Sklearn: {sklearn_final:12} ({sklearn_conf:.3f}) | ONNX: {onnx_final:12} ({onnx_conf:.3f}) {match}")
        
    except Exception as e:
        print(f"  ⚠️  Could not compare with sklearn model: {e}")
    
    return True

if __name__ == "__main__":
    debug_onnx_model()