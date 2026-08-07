"""
=============================================================================
NutriAI - Local ONNX Model Tester Script
=============================================================================

Test your trained `food_classifier.onnx` model on any food image!

Usage:
  python3 test_local_model.py --image path/to/food_image.jpg
"""

import os
import sys
import json
import argparse
import numpy as np
from PIL import Image
import onnxruntime as ort

def test_model(image_path: str, model_path: str, labels_path: str):
    if not os.path.exists(image_path):
        print(f"Error: Image '{image_path}' not found.")
        sys.exit(1)

    if not os.path.exists(model_path) or not os.path.exists(labels_path):
        print(f"Error: Model file '{model_path}' or labels file '{labels_path}' missing.")
        sys.exit(1)

    # 1. Load Labels
    with open(labels_path, "r", encoding="utf-8") as f:
        labels = json.load(f)

    # 2. Load ONNX Model
    print(f"Loading ONNX Model: {model_path}")
    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    # 3. Preprocess Image (ImageNet standard normalization)
    print(f"Processing image: {image_path}")
    img = Image.open(image_path).convert("RGB")
    img_resized = img.resize((224, 224), Image.Resampling.BILINEAR)

    img_np = np.array(img_resized, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img_np = (img_np - mean) / std

    # Reshape from (H, W, C) to (1, C, H, W)
    img_tensor = np.transpose(img_np, (2, 0, 1))
    img_tensor = np.expand_dims(img_tensor, axis=0).astype(np.float32)

    # 4. Run ONNX Inference
    outputs = session.run(None, {input_name: img_tensor})
    logits = outputs[0][0]

    # Compute Softmax probabilities
    exp_logits = np.exp(logits - np.max(logits))
    probs = exp_logits / np.sum(exp_logits)

    # Get Top-5 Predictions
    top_indices = np.argsort(probs)[::-1][:5]

    print("\n" + "=" * 50)
    print("TOP PREDICTIONS FOR IMAGE:")
    print("=" * 50)
    for rank, idx in enumerate(top_indices, 1):
        class_name = labels.get(str(idx), labels.get(idx, f"Class_{idx}"))
        formatted_name = class_name.replace("_", " ").title()
        score = probs[idx] * 100
        bar = "█" * int(score / 5)
        print(f"{rank}. {formatted_name:<25} | {score:6.2f}% {bar}")
    print("=" * 50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Test trained local ONNX food classifier")
    parser.add_argument("--image", type=str, required=True, help="Path to input image file")
    parser.add_argument("--model", type=str, default="backend/models/food_classifier.onnx", help="Path to ONNX model")
    parser.add_argument("--labels", type=str, default="backend/models/labels.json", help="Path to labels JSON")
    
    args = parser.parse_args()
    test_model(args.image, args.model, args.labels)

if __name__ == "__main__":
    main()
