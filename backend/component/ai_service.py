import os
import google.generativeai as genai
import json
import re
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

# Use the flash model for multimodal and fast reasoning (fallback to gemini-1.5-flash)
AI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
model = genai.GenerativeModel(AI_MODEL)


USDA_API_KEY = os.getenv("USDA_API_KEY")

from component.common_foods import COMMON_FOODS

def get_alternatives_for_allergy(allergy: str) -> str:
    alts = {
        "peanut": "almonds, sunflower seeds, or pumpkin seeds",
        "peanuts": "almonds, sunflower seeds, or pumpkin seeds",
        "shellfish": "fish, chicken, or tofu",
        "shrimp": "fish, chicken, or tofu",
        "crab": "fish, chicken, or tofu",
        "milk": "almond milk, soy milk, or oat milk",
        "dairy": "almond milk, soy milk, or oat milk",
        "egg": "chia seeds, applesauce (for baking), or tofu",
        "eggs": "chia seeds, applesauce (for baking), or tofu",
        "wheat": "quinoa, rice, or gluten-free oats",
        "soy": "lentils, chickpeas, or coconut aminos",
        "fish": "chicken, tofu, or legumes"
    }
    return alts.get(allergy.lower(), "safe vegetables, lean meats, or other allergen-free options")

def check_local_medical_cautions(food_key: str, medical_profile: dict) -> str:
    if not medical_profile:
        return None
        
    illnesses = (medical_profile.get("illnesses") or "").lower()
    allergies = (medical_profile.get("allergies") or "").lower()
    
    allergy_list = [a.strip() for a in allergies.split(",") if a.strip()]
    for allergy in allergy_list:
        if allergy in food_key or food_key in allergy:
            alts = get_alternatives_for_allergy(allergy)
            return f"Contains {allergy.capitalize()}, caution for allergies. Suggested alternatives: {alts}."
            
    if "diabetes" in illnesses:
        high_carb_foods = ["banana", "apple", "white rice", "brown rice", "potato", "sweet potato", "oats", "pancit", "spaghetti", "macaroni"]
        if food_key in high_carb_foods:
            return "High carbohydrate/sugar content, caution for Diabetes. Suggested alternatives: leafy greens, cauliflower rice, lean proteins, or quinoa."
            
    if "lactose intolerance" in illnesses:
        if food_key in ["milk", "cheese", "butter", "cream"]:
            return "Contains lactose, caution for Lactose Intolerance. Suggested alternatives: almond milk, soy milk, oat milk, or lactose-free products."
            
    return None

def find_local_food(query: str, medical_profile: dict = None) -> json.dumps:
    q = query.strip().lower()
    
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams|ml)\b', q)
    food_name = q
    weight = None
    count = None
    
    if weight_match:
        weight = float(weight_match.group(1))
        food_name = re.sub(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams|ml)\b', '', q).strip()
    else:
        count_match = re.match(r'^(\d+(?:\.\d+)?)\s+(.*)', q)
        if count_match:
            count = float(count_match.group(1))
            food_name = count_match.group(2).strip()
        else:
            word_numbers = {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0}
            words = q.split()
            if words and words[0] in word_numbers:
                count = word_numbers[words[0]]
                food_name = " ".join(words[1:]).strip()

    food_name = re.sub(r'[^a-zA-Z0-9\s]', '', food_name).strip()
    
    matched_key = None
    matched_food = None
    
    # 1. Exact match
    for key, food_info in COMMON_FOODS.items():
        if food_name == key or food_name in food_info.get("synonyms", []):
            matched_key = key
            matched_food = food_info
            break
            
    # 2. Singular/Plural match
    if not matched_food and food_name.endswith('s'):
        singular = food_name[:-1]
        for key, food_info in COMMON_FOODS.items():
            if singular == key or singular in food_info.get("synonyms", []):
                matched_key = key
                matched_food = food_info
                break

    # 3. Partial/Substring match (e.g. 'kare kare' matches 'kare-kare' or 'beef kare kare')
    if not matched_food and len(food_name) >= 3:
        for key, food_info in COMMON_FOODS.items():
            clean_key = key.replace("-", " ")
            if food_name in key or key in food_name or food_name in clean_key or clean_key in food_name:
                matched_key = key
                matched_food = food_info
                break
            synonyms = food_info.get("synonyms", [])
            if any(food_name in s or s in food_name for s in synonyms):
                matched_key = key
                matched_food = food_info
                break

    if matched_food:
        calculated_weight = 100.0
        if weight is not None:
            calculated_weight = weight
        elif count is not None:
            serving_weight = matched_food.get("serving_weight", 100.0)
            calculated_weight = count * serving_weight
        else:
            if "serving_weight" in matched_food:
                calculated_weight = matched_food["serving_weight"]
                
        scale = calculated_weight / 100.0
        caution = check_local_medical_cautions(matched_key, medical_profile)
        
        return {
            "food_name": f"{matched_food['name']} ({int(calculated_weight)}g)" if weight is not None or count is not None else matched_food['name'],
            "calories": int(round(matched_food["calories"] * scale)),
            "protein_g": round(matched_food["protein_g"] * scale, 1),
            "carbs_g": round(matched_food["carbs_g"] * scale, 1),
            "fat_g": round(matched_food["fat_g"] * scale, 1),
            "vitamin_c_mg": round(matched_food["vitamin_c_mg"] * scale, 2),
            "calcium_mg": round(matched_food["calcium_mg"] * scale, 1),
            "iron_mg": round(matched_food["iron_mg"] * scale, 2),
            "caution_warning": caution
        }
        
    return None

def search_usda_database(query: str, api_key: str, medical_profile: dict = None) -> json.dumps:
    q = query.strip().lower()
    
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams|ml)\b', q)
    food_name = q
    weight = None
    count = None
    
    if weight_match:
        weight = float(weight_match.group(1))
        food_name = re.sub(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams|ml)\b', '', q).strip()
    else:
        count_match = re.match(r'^(\d+(?:\.\d+)?)\s+(.*)', q)
        if count_match:
            count = float(count_match.group(1))
            food_name = count_match.group(2).strip()
        else:
            word_numbers = {"one": 1.0, "two": 2.0, "three": 3.0, "four": 4.0, "five": 5.0}
            words = q.split()
            if words and words[0] in word_numbers:
                count = word_numbers[words[0]]
                food_name = " ".join(words[1:]).strip()
                
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "api_key": api_key,
        "query": food_name,
        "pageSize": 1
    }
    
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code != 200:
            print(f"USDA API failed: {res.status_code}")
            return None
            
        data = res.json()
        if not data.get("foods"):
            return None
            
        food = data["foods"][0]
        
        nutrients = {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fat_g": 0.0,
            "vitamin_c_mg": 0.0,
            "calcium_mg": 0.0,
            "iron_mg": 0.0
        }
        
        for n in food.get("foodNutrients", []):
            nid = n.get("nutrientId")
            val = n.get("value", 0.0)
            if nid == 1008:
                nutrients["calories"] = val
            elif nid == 1003:
                nutrients["protein_g"] = val
            elif nid == 1005:
                nutrients["carbs_g"] = val
            elif nid == 1004:
                nutrients["fat_g"] = val
            elif nid == 1162:
                nutrients["vitamin_c_mg"] = val
            elif nid == 1087:
                nutrients["calcium_mg"] = val
            elif nid == 1089:
                nutrients["iron_mg"] = val
                
        calculated_weight = 100.0
        if weight is not None:
            calculated_weight = weight
        elif count is not None:
            calculated_weight = count * 100.0
            
        scale = calculated_weight / 100.0
        desc_lower = food.get("description", "").lower()
        caution = check_local_medical_cautions(desc_lower, medical_profile)
        
        return {
            "food_name": f"{food.get('description')} ({int(calculated_weight)}g)" if weight is not None or count is not None else food.get('description'),
            "calories": int(round(nutrients["calories"] * scale)),
            "protein_g": round(nutrients["protein_g"] * scale, 1),
            "carbs_g": round(nutrients["carbs_g"] * scale, 1),
            "fat_g": round(nutrients["fat_g"] * scale, 1),
            "vitamin_c_mg": round(nutrients["vitamin_c_mg"] * scale, 2),
            "calcium_mg": round(nutrients["calcium_mg"] * scale, 1),
            "iron_mg": round(nutrients["iron_mg"] * scale, 2),
            "caution_warning": caution
        }
    except Exception as e:
        print(f"USDA Database error: {e}")
        return None

# Initialize lazy-loaded global OCR engine
ocr_engine = None

def compress_image_for_ai(image_bytes: bytes, max_dim: int = 1024, quality: int = 75) -> bytes:
    """
    Compresses image bytes by scaling the image down so its maximum dimension is max_dim (preserving aspect ratio)
    and saving as JPEG at the specified quality level.
    """
    try:
        from PIL import Image
        import io
        
        # Read image
        img = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed (since JPEG does not support RGBA alpha channels)
        if img.mode != "RGB":
            img = img.convert("RGB")
            
        width, height = img.size
        # Resize if dimensions exceed max_dim
        if width > max_dim or height > max_dim:
            if width > height:
                new_width = max_dim
                new_height = int(round(height * (max_dim / width)))
            else:
                new_height = max_dim
                new_width = int(round(width * (max_dim / height)))
                
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
        # Compress
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=quality, optimize=True)
        compressed_bytes = out_buf.getvalue()
        
        orig_sz = len(image_bytes)
        comp_sz = len(compressed_bytes)
        reduction = (1 - comp_sz / orig_sz) * 100 if orig_sz > 0 else 0
        print(f"Image compressed: {orig_sz / 1024:.1f} KB -> {comp_sz / 1024:.1f} KB ({reduction:.1f}% reduction)")
        
        return compressed_bytes
    except Exception as e:
        print(f"Error during image preprocessing/compression: {e}")
        # Return original bytes if anything fails
        return image_bytes

def init_ocr_engine():
    """
    Eagerly loads and initializes the local OCR engine.
    """
    global ocr_engine
    if ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr_engine = RapidOCR()
            print("Successfully initialized RapidOCR engine.")
        except Exception as e:
            try:
                from rapidocr import RapidOCR
                ocr_engine = RapidOCR()
                print("Successfully initialized RapidOCR (fallback package).")
            except Exception as e2:
                print(f"Failed to load RapidOCR: {e} | {e2}")

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extracts text from image bytes using a local RapidOCR engine.
    """
    init_ocr_engine()
    if ocr_engine is None:
        return ""

    try:
        from PIL import Image
        import numpy as np
        import io

        image = Image.open(io.BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")

        img_array = np.array(image)
        result, _ = ocr_engine(img_array)

        if not result:
            return ""

        # result format: [[box, text, confidence], ...]
        texts = [res[1] for res in result if res and len(res) > 1]
        return "\n".join(texts)
    except Exception as e:
        print(f"Error during local OCR extraction: {e}")
        return ""

# --- Local Vision ML Model (MobileNetV3-Large ONNX) ---
onnx_vision_session = None
onnx_model_labels = {}

def init_local_vision_model(force_reload: bool = False):
    """
    Lazy-loads ONNX Runtime inference session for MobileNetV3-Large food classifier.
    Supports force_reload=True for in-memory hot-reloading after automated retraining.
    """
    global onnx_vision_session, onnx_model_labels
    if onnx_vision_session is not None and not force_reload:
        return

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_onnx = os.path.join(base_dir, "models", "food_classifier.onnx")
    default_labels = os.path.join(base_dir, "models", "labels.json")

    onnx_path = os.getenv("LOCAL_MODEL_PATH", default_onnx)
    labels_path = os.getenv("LOCAL_LABELS_PATH", default_labels)

    # Fallback to default absolute paths if relative env paths fail to resolve
    if not os.path.exists(onnx_path) and os.path.exists(default_onnx):
        onnx_path = default_onnx
    if not os.path.exists(labels_path) and os.path.exists(default_labels):
        labels_path = default_labels

    if not os.path.exists(onnx_path) or not os.path.exists(labels_path):
        print(f"Warning: Model file not found at '{onnx_path}' or labels at '{labels_path}'")
        return

    try:
        import onnxruntime as ort
        onnx_vision_session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
        with open(labels_path, "r", encoding="utf-8") as f:
            onnx_model_labels = json.load(f)
        print(f"Successfully loaded local MobileNetV3-Large ONNX vision model from '{onnx_path}' ({len(onnx_model_labels)} classes).")
    except Exception as e:
        print(f"Notice: Local ONNX vision model could not be loaded ({e}).")


import hashlib

def collect_training_sample(image_bytes: bytes, food_name: str):
    """
    Saves uploaded image bytes and Gemini-verified food label into local training_cache
    for automated model retraining.
    """
    if not image_bytes or not food_name:
        return
    try:
        clean_label = re.sub(r'[^a-zA-Z0-9]', '_', food_name.strip().lower()).strip('_')
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        target_dir = os.path.join(base_dir, "training_cache", "images", clean_label)
        os.makedirs(target_dir, exist_ok=True)
        
        img_hash = hashlib.sha256(image_bytes).hexdigest()[:16]
        img_path = os.path.join(target_dir, f"{img_hash}.jpg")
        
        if not os.path.exists(img_path):
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            print(f"Saved new training image sample for category '{clean_label}'.")
    except Exception as e:
        print(f"Notice: Failed to save training sample ({e})")

def classify_food_image_local(image_bytes: bytes):
    """
    Executes local MobileNetV3-Large ONNX model on uploaded image bytes.
    Returns tuple (raw_class_name, confidence_score) or None if model unavailable.
    """
    init_local_vision_model()
    if onnx_vision_session is None or not onnx_model_labels:
        return None

    try:
        from PIL import Image
        import numpy as np
        import io

        # 1. Load image and convert to RGB
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224), Image.Resampling.BILINEAR)

        # 2. Normalize image with ImageNet mean and std
        img_np = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_np = (img_np - mean) / std

        # Transpose from (H, W, C) to (1, C, H, W) for ONNX input
        img_tensor = np.transpose(img_np, (2, 0, 1))
        img_tensor = np.expand_dims(img_tensor, axis=0).astype(np.float32)

        # 3. Execute ONNX inference
        input_name = onnx_vision_session.get_inputs()[0].name
        outputs = onnx_vision_session.run(None, {input_name: img_tensor})
        logits = outputs[0][0]

        # 4. Compute Softmax probabilities
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])

        raw_label = onnx_model_labels.get(str(top_idx), onnx_model_labels.get(top_idx, "unknown_food"))
        return raw_label, confidence
    except Exception as e:
        print(f"Error during local ML vision classification: {e}")
        return None

def analyze_food_multimodal(food_text: str, image_bytes: bytes, mime_type: str, medical_profile: dict = None):
    """
    Analyzes food input (image and/or text) using the local trained vision model and local databases.
    If an image is uploaded, it evaluates the trained local MobileNetV3 ONNX model FIRST.
    Gemini API calls are completely omitted.
    """
    # -------------------------------------------------------------------------
    # PATHWAY 1: Image Uploaded -> ALWAYS Check Trained Vision ML Model FIRST
    # -------------------------------------------------------------------------
    if image_bytes:
        print("Image uploaded. Running local trained ONNX vision model...")
        ml_pred = classify_food_image_local(image_bytes)
        
        if ml_pred:
            raw_class, confidence = ml_pred
            threshold = float(os.getenv("LOCAL_ML_CONFIDENCE_THRESHOLD", "0.40"))
            from component.food101_mapping import format_class_name, get_nutrition_for_class
            display_name = format_class_name(raw_class)
            
            print(f"Local Vision ML Model Output: Class='{raw_class}' ({display_name}), Confidence={confidence*100:.1f}%, Threshold={threshold*100:.0f}%")
            
            if confidence >= threshold:
                print(f"SUCCESS: Local Vision Model HIT! '{display_name}' ({confidence*100:.1f}% confidence >= {threshold*100:.0f}% threshold).")
                
                # Check local food DB first with human-readable food name
                local_food_res = find_local_food(display_name, medical_profile)
                if local_food_res:
                    local_food_res["source"] = "local_ml_model"
                    local_food_res["confidence"] = round(confidence, 2)
                    return local_food_res
                
                # Fallback to class nutritional profile mapping
                nutrition_data = get_nutrition_for_class(raw_class)
                caution = check_local_medical_cautions(display_name.lower(), medical_profile)
                nutrition_data["caution_warning"] = caution
                nutrition_data["source"] = "local_ml_model"
                nutrition_data["confidence"] = round(confidence, 2)
                return nutrition_data
            else:
                print(f"Local Vision ML confidence score ({confidence*100:.1f}%) is below threshold ({threshold*100:.0f}%).")

        # Optional OCR fallback if vision confidence was below threshold
        ocr_text = extract_text_from_image(image_bytes)
        search_query = food_text.strip() if food_text else ocr_text.strip()
        if search_query:
            local_result = find_local_food(search_query, medical_profile)
            if local_result:
                local_result["source"] = "local_database"
                return local_result

        raise HTTPException(
            status_code=404,
            detail="Food not found in dataset. The uploaded image could not be identified with sufficient confidence."
        )

    # -------------------------------------------------------------------------
    # PATHWAY 2: Text Search Only (No Image Uploaded)
    # -------------------------------------------------------------------------
    search_query = food_text.strip() if food_text else ""
    if search_query:
        print(f"Searching local common foods database for text query: '{search_query}'")
        
        # 1. Search local common foods dictionary (exact + fuzzy/synonym)
        local_result = find_local_food(search_query, medical_profile)
        if local_result:
            local_result["source"] = "local_database"
            return local_result

        # 2. Search trained dataset labels (labels.json)
        from component.food101_mapping import format_class_name, get_nutrition_for_class
        clean_q = re.sub(r'[^a-zA-Z0-9]', '', search_query.lower())
        init_local_vision_model()
        if onnx_model_labels:
            for idx_str, raw_cls in onnx_model_labels.items():
                clean_cls = raw_cls.replace('_', '').lower()
                if clean_q in clean_cls or clean_cls in clean_q:
                    display_name = format_class_name(raw_cls)
                    print(f"Text Match against trained model label '{raw_cls}' -> '{display_name}'")
                    nutrition_data = get_nutrition_for_class(raw_cls)
                    caution = check_local_medical_cautions(display_name.lower(), medical_profile)
                    nutrition_data["caution_warning"] = caution
                    nutrition_data["source"] = "local_database"
                    return nutrition_data

        # 3. Search USDA Database if key configured
        if USDA_API_KEY and USDA_API_KEY != "your_usda_api_key_here":
            usda_result = search_usda_database(search_query, USDA_API_KEY, medical_profile)
            if usda_result:
                usda_result["source"] = "usda_database"
                return usda_result

    print(f"Food text query '{food_text}' not found in local dataset.")
    raise HTTPException(
        status_code=404,
        detail=f"Food '{food_text}' not found in dataset. Please upload a clear image of a supported Philippine food or enter a recognized item."
    )