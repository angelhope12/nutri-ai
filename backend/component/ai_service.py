import os
import json
import re
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables from .env file
load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY")

from component.common_foods import COMMON_FOODS

def check_local_medical_cautions(food_key: str, medical_profile: dict, scale: float = 1.0) -> str:
    """Dynamically checks allergies and medical conditions against COMMON_FOODS and suggests safe dataset alternatives."""
    if not medical_profile:
        return None
    ignored_values = {'none', 'n/a', 'na', 'no', 'no allergies', 'no allergy', 'nothing', 'nil', 'null', '-', 'wala'}
    allergies = [a.strip().lower() for a in (medical_profile.get('allergies') or '').split(',') if a.strip() and a.strip().lower() not in ignored_values]
    illnesses = [a.strip() for a in (medical_profile.get('illnesses') or '').split(',') if a.strip() and a.strip().lower() not in ignored_values]
    if not allergies and not illnesses:
        return None

    allergen_keywords = {
        'peanut': ['peanut', 'kare kare', 'kare-kare', 'lumpiang sariwa'],
        'peanuts': ['peanut', 'kare kare', 'kare-kare', 'lumpiang sariwa'],
        'nut': ['peanut', 'nut', 'kare kare', 'kare-kare'],
        'nuts': ['peanut', 'nut', 'kare kare', 'kare-kare'],
        'shrimp': ['shrimp', 'hipon', 'palabok', 'malabon', 'bicol express', 'pinakbet', 'kare kare'],
        'hipon': ['shrimp', 'hipon', 'palabok', 'malabon', 'bicol express', 'pinakbet'],
        'shellfish': ['shrimp', 'hipon', 'crab', 'alimango', 'pusit', 'squid', 'tahong', 'palabok', 'malabon', 'bicol express', 'pinakbet'],
        'seafood': ['shrimp', 'hipon', 'crab', 'pusit', 'squid', 'fish', 'isda', 'bangus', 'tilapia', 'tanigue', 'tuyo', 'daing', 'palabok', 'malabon'],
        'crab': ['crab', 'alimango', 'palabok', 'malabon'],
        'squid': ['squid', 'pusit', 'calamares'],
        'pusit': ['squid', 'pusit', 'calamares'],
        'fish': ['fish', 'isda', 'bangus', 'tilapia', 'tanigue', 'tuyo', 'daing', 'bangsilog', 'tinapa', 'salmon', 'tuna'],
        'isda': ['fish', 'isda', 'bangus', 'tilapia', 'tanigue', 'tuyo', 'daing', 'bangsilog'],
        'egg': ['egg', 'itlog', 'balut', 'kwek', 'tortang', 'leche flan', 'silog', 'tapsilog', 'longsilog', 'tocilog', 'bangsilog', 'lomi', 'arroz caldo'],
        'eggs': ['egg', 'itlog', 'balut', 'kwek', 'tortang', 'leche flan', 'silog', 'tapsilog', 'longsilog', 'tocilog', 'bangsilog', 'lomi', 'arroz caldo'],
        'milk': ['milk', 'dairy', 'cheese', 'butter', 'cream', 'leche flan', 'halo halo', 'mango float', 'buko pandan', 'sopas', 'ensaymada', 'cassava cake'],
        'dairy': ['milk', 'dairy', 'cheese', 'butter', 'cream', 'leche flan', 'halo halo', 'mango float', 'buko pandan', 'sopas', 'ensaymada', 'cassava cake'],
        'pork': ['pork', 'baboy', 'lechon', 'sisig', 'pata', 'menudo', 'dinuguan', 'tocino', 'longganisa', 'longsilog', 'tocilog', 'chicharon', 'bicol express', 'lumpia shanghai', 'lomi', 'batchoy'],
        'baboy': ['pork', 'baboy', 'lechon', 'sisig', 'pata', 'menudo', 'dinuguan', 'tocino', 'longganisa', 'longsilog', 'tocilog', 'chicharon'],
        'chicken': ['chicken', 'manok', 'inasal', 'tinola', 'sopas', 'afritada', 'arroz caldo'],
        'manok': ['chicken', 'manok', 'inasal', 'tinola', 'sopas', 'afritada', 'arroz caldo'],
        'beef': ['beef', 'baka', 'caldereta', 'kaldereta', 'bistek', 'pares', 'bulalo', 'tapsilog', 'tapa'],
        'baka': ['beef', 'baka', 'caldereta', 'kaldereta', 'bistek', 'pares', 'bulalo', 'tapsilog', 'tapa'],
        'soy': ['soy', 'tofu', 'tokwa', 'taho', 'adobo', 'bistek', 'pares'],
        'wheat': ['wheat', 'bread', 'pandesal', 'ensaymada', 'pan de coco', 'hopia', 'pancit', 'lomi', 'batchoy', 'spaghetti', 'lumpia', 'turon', 'oats'],
        'gluten': ['wheat', 'bread', 'pandesal', 'ensaymada', 'pan de coco', 'hopia', 'pancit', 'lomi', 'batchoy', 'spaghetti', 'lumpia', 'turon', 'oats'],
    }

    def _matches_allergy(target_name: str, allergy_term: str) -> bool:
        t = target_name.lower().replace('_', ' ')
        base = allergy_term.lower().strip()
        if re.search(r'\b' + re.escape(base.rstrip('s')) + r's?\b', t):
            return True
        for kw in allergen_keywords.get(base, []):
            if kw in t:
                return True
        return False

    def _violates_illness(target_name: str, info: dict, illness_list: list) -> list:
        t = target_name.lower().replace('_', ' ')
        cals = float(info.get('calories', 200))
        carbs = float(info.get('carbs_g', 15))
        fat = float(info.get('fat_g', 10))
        prot = float(info.get('protein_g', 12))
        reasons = []
        for ill in illness_list:
            il = ill.lower()
            if 'diabetes' in il:
                sweet_or_starchy = any(w in t for w in ['halo', 'leche', 'ube', 'biko', 'cassava', 'float', 'buko pandan', 'turon', 'banana cue', 'spaghetti', 'tocino', 'taho', 'sapin', 'puto', 'bibingka', 'bread', 'ensaymada', 'pan de coco', 'hopia', 'pandesal', 'rice', 'silog', 'pancit'])
                if carbs >= 25.0 or sweet_or_starchy:
                    reasons.append(f"High carbohydrate/sugar content ({carbs:.0f}g carbs), caution for {ill}")
            if any(k in il for k in ['hypertension', 'heart', 'cholesterol', 'blood pressure']):
                fatty_or_salty = any(w in t for w in ['lechon', 'crispy pata', 'sisig', 'chicharon', 'bulalo', 'dinuguan', 'bicol express', 'tuyo', 'daing', 'tocino', 'longganisa', 'longsilog', 'tocilog', 'tapsilog', 'isaw', 'kwek', 'pares', 'caldereta'])
                if fat >= 16.0 or fatty_or_salty:
                    reasons.append(f"High fat/sodium content ({fat:.0f}g fat), caution for {ill}")
            if 'obesity' in il:
                if cals >= 260 or fat >= 16.0:
                    reasons.append(f"High calorie/fat density ({cals:.0f} kcal), caution for {ill}")
            if 'kidney' in il:
                if prot >= 23.0 or any(w in t for w in ['tuyo', 'daing', 'tocino', 'longganisa', 'sisig']):
                    reasons.append(f"High protein/sodium load, caution for {ill}")
            if 'celiac' in il or 'gluten' in il:
                if _matches_allergy(t, 'gluten'):
                    reasons.append(f"Contains wheat/gluten, caution for {ill}")
            if 'lactose' in il:
                if _matches_allergy(t, 'dairy'):
                    reasons.append(f"Contains dairy/lactose, caution for {ill}")
            if 'gout' in il or 'uric' in il:
                if any(w in t for w in ['chicharon', 'isaw', 'dinuguan', 'sisig', 'bulalo', 'pata', 'beef', 'baka', 'hipon', 'pusit', 'balut']):
                    reasons.append(f"High purine content, caution for {ill}")
        return reasons

    name = food_key.lower().replace('_', ' ').strip()
    food_info = COMMON_FOODS.get(name)
    if not food_info:
        for k, v in COMMON_FOODS.items():
            if name == k or name in v.get('synonyms', []):
                food_info = v
                break
    food_info = dict(food_info) if food_info else {}
    if food_info and scale != 1.0:
        for k in ('calories', 'protein_g', 'carbs_g', 'fat_g'):
            if k in food_info:
                food_info[k] = round(float(food_info[k]) * scale, 1)

    sections = []
    triggered_allergy = False
    matched_allergies = []
    for allergy in allergies:
        if _matches_allergy(name, allergy):
            matched_allergies.append(allergy.title())
            triggered_allergy = True

    if matched_allergies:
        sections.append(f"🚨 Allergy Alert: Possible {', '.join(matched_allergies)} match in {food_info.get('name', food_key.title())}.")

    illness_reasons = _violates_illness(name, food_info, illnesses)
    for reason in illness_reasons:
        sections.append(f"🩺 {reason}.")

    # Dynamically select safer alternatives from COMMON_FOODS / labels.json when an allergy or illness caution is triggered
    if triggered_allergy or illness_reasons:
        label_keys = set()
        try:
            labels_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "labels.json")
            if os.path.exists(labels_path):
                with open(labels_path, "r", encoding="utf-8") as lf:
                    ldata = json.load(lf)
                label_keys = {str(v).lower().replace('_', ' ').strip() for v in ldata.values()}
        except Exception:
            pass

        target_cals = float(food_info.get('calories', 220))
        target_prot = float(food_info.get('protein_g', 18))
        target_carbs = float(food_info.get('carbs_g', 12))
        target_fat = float(food_info.get('fat_g', 12))
        unhealthy_alts = {'balut', 'tuyo', 'tuyo dried fish', 'chicharon bulaklak', 'isaw bbq', 'kwek kwek', 'crispy pata', 'lechon baboy', 'lechon kawali', 'pork sisig', 'dinuguan'}

        candidates = []
        for cand_key, cand_info in COMMON_FOODS.items():
            if cand_key == name or name in cand_info.get('synonyms', []):
                continue
            if cand_key in unhealthy_alts:
                continue
            if any(_matches_allergy(cand_key, a) for a in allergies):
                continue
            if _violates_illness(cand_key, cand_info, illnesses):
                continue

            in_labels = 0 if (not label_keys or cand_key in label_keys or any(s in label_keys for s in cand_info.get('synonyms', []))) else 1
            cand_cals = float(cand_info.get('calories', 200))
            cand_prot = float(cand_info.get('protein_g', 15))
            cand_carbs = float(cand_info.get('carbs_g', 15))
            cand_fat = float(cand_info.get('fat_g', 10))

            macro_distance = (
                abs(cand_prot - target_prot) * 2.5
                + abs(cand_carbs - target_carbs) * 1.8
                + abs(cand_fat - target_fat) * 1.8
                + abs(cand_cals - target_cals) * 0.15
            )
            score = (in_labels, round(macro_distance, 2))
            cname = f"{cand_info.get('name', cand_key.title())} — {int(cand_cals)} kcal · {cand_prot:g}g P · {cand_carbs:g}g C · {cand_fat:g}g F"
            candidates.append((score, cname))

        candidates.sort(key=lambda x: x[0])
        top_alts = []
        for _, cname in candidates:
            if cname not in top_alts:
                top_alts.append(cname)
            if len(top_alts) == 3:
                break
        if top_alts:
            alt_lines = "\n".join(f"• {alt}" for alt in top_alts)
            sections.append(f"🥗 Safer Alternatives (Similar Macros):\n{alt_lines}")

    if allergies and not triggered_allergy:
        sections.append("🛡️ Allergy check: " + ", ".join(a.title() for a in allergies) + ".")
    if illnesses and not illness_reasons:
        sections.append("📋 Saved conditions (" + ", ".join(illnesses) + "): follow your clinician’s portion guidance.")

    return "\n".join(sections) if sections else None


def find_local_food(query: str, medical_profile: dict = None) -> json.dumps:
    q = query.strip().lower()
    if re.search(r'(?<![a-z])(?:ml|liters?|litres?|cups?|tbsp|tsp|oz|kg|lbs?)\b', q):
        raise HTTPException(status_code=422, detail="Please provide the portion in grams; volume and other unit conversions are not available.")
    if re.search(r'(?:^|\s)-\s*\d', q):
        raise HTTPException(status_code=422, detail="Portion must be positive.")
    
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b', q)
    food_name = q
    weight = None
    count = None
    
    if weight_match:
        weight = float(weight_match.group(1))
        food_name = re.sub(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b', '', q).strip()
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

    if (weight is not None and weight <= 0) or (count is not None and count <= 0):
        raise HTTPException(status_code=422, detail="Portion must be positive.")
    food_name = ' '.join(re.sub(r'[^a-zA-Z0-9\s]', ' ', food_name).split())
    
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

    if matched_food:
        calculated_weight = 100.0
        if weight is not None:
            calculated_weight = weight
        elif count is not None:
            if "serving_weight" not in matched_food:
                raise HTTPException(status_code=422, detail="This food has no known piece weight. Please enter grams.")
            serving_weight = matched_food["serving_weight"]
            calculated_weight = count * serving_weight
        else:
            if "serving_weight" in matched_food:
                calculated_weight = matched_food["serving_weight"]
                
        per_100g_items = {"chicken breast", "egg", "banana", "apple", "white rice", "brown rice", "oats", "milk", "broccoli", "salmon", "beef", "potato", "sweet potato", "avocado"}
        base_weight = 100.0 if matched_key in per_100g_items else float(matched_food.get("serving_weight", 100.0))
        scale = calculated_weight / base_weight
        caution = check_local_medical_cautions(matched_key, medical_profile, scale=scale)
        
        return {
            "food_name": f"{matched_food['name']} ({int(calculated_weight)}g)" if weight is not None or count is not None else matched_food['name'],
            "calories": int(round(matched_food["calories"] * scale)),
            "protein_g": round(matched_food["protein_g"] * scale, 1),
            "carbs_g": round(matched_food["carbs_g"] * scale, 1),
            "fat_g": round(matched_food["fat_g"] * scale, 1),
            "vitamin_c_mg": round(matched_food["vitamin_c_mg"] * scale, 2),
            "calcium_mg": round(matched_food["calcium_mg"] * scale, 1),
            "iron_mg": round(matched_food["iron_mg"] * scale, 2),
            "portion_grams": calculated_weight,
            "portion_assumed": weight is None and count is None,
            "is_estimate": True,
            "caution_warning": caution
        }
        
    return None

def search_usda_database(query: str, api_key: str, medical_profile: dict = None) -> json.dumps:
    q = query.strip().lower()
    if re.search(r'(?<![a-z])(?:ml|liters?|litres?|cups?|tbsp|tsp|oz|kg|lbs?)\b', q):
        raise HTTPException(status_code=422, detail="Please provide the portion in grams; volume and other unit conversions are not available.")
    if re.search(r'(?:^|\s)-\s*\d', q):
        raise HTTPException(status_code=422, detail="Portion must be positive.")
    
    weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b', q)
    food_name = q
    weight = None
    count = None
    
    if weight_match:
        weight = float(weight_match.group(1))
        food_name = re.sub(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b', '', q).strip()
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
            raise HTTPException(status_code=422, detail="Please enter grams for USDA results; piece weights are unknown.")
            
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
    except HTTPException:
        raise
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
        from component.sync_common_foods import sync_labels_to_common_foods
        sync_labels_to_common_foods(onnx_model_labels)
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
        # Match validation Resize(256) + CenterCrop(224), preserving aspect ratio.
        width, height = img.size
        if width <= height:
            size = (256, int(256 * height / width))
        else:
            size = (int(256 * width / height), 256)
        img = img.resize(size, Image.Resampling.BILINEAR)
        left = round((img.width - 224) / 2)
        top = round((img.height - 224) / 2)
        img = img.crop((left, top, left + 224, top + 224))

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

def analyze_food_multimodal(food_text: str, image_bytes: bytes, mime_type: str, medical_profile: dict = None, portion_grams: float = None):
    """
    Analyzes food input (image and/or text) using the local trained vision model and local databases.
    If an image is uploaded, it evaluates the trained local MobileNetV3 ONNX model FIRST.
    Gemini API calls are completely omitted.
    """
    if portion_grams is not None and portion_grams <= 0:
        raise HTTPException(status_code=422, detail="Portion must be positive.")

    if image_bytes and food_text and food_text.strip():
        # If food_text is only a gram weight (e.g. "250g" or "250"), treat it as portion_grams for the image
        only_weight = re.match(r'^\s*(\d+(?:\.\d+)?)\s*(?:g|gram|grams)?\s*$', food_text.strip(), re.I)
        if only_weight:
            if portion_grams is None:
                portion_grams = float(only_weight.group(1))
            food_text = None
        else:
            return analyze_food_multimodal(food_text, None, None, medical_profile, portion_grams=portion_grams)

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
                
                lookup_query = f"{portion_grams:g}g {display_name}" if portion_grams else display_name
                # Check local food DB first with human-readable food name (and optional grams)
                local_food_res = find_local_food(lookup_query, medical_profile)
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
    if search_query and portion_grams and not re.search(r'(\d+(?:\.\d+)?)\s*(?:g|gram|grams)\b', search_query, re.I):
        search_query = f"{portion_grams:g}g {search_query}"
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
                if clean_q and clean_q == clean_cls:
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
