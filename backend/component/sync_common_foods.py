"""
Automatically synchronizes food labels from labels.json into backend/component/common_foods.py.
Triggered automatically after model training (export_to_onnx) and on backend model load.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


def _estimate_nutrition_from_keywords(clean_key: str, display_name: str) -> Dict[str, Any]:
    """
    Infers reasonable per-100g nutritional macros and default serving weight based on
    Filipino/English dish keywords when an external nutrition API is unavailable.
    """
    text = clean_key.lower()

    # Default balanced Filipino dish profile
    profile = {
        "serving_weight": 200.0,
        "calories": 210,
        "protein_g": 14.0,
        "carbs_g": 12.0,
        "fat_g": 11.0,
        "vitamin_c_mg": 3.0,
        "calcium_mg": 35.0,
        "iron_mg": 1.5,
    }

    if any(k in text for k in ["silog", "fried rice", "sinangag", "arroz", "champorado", "lugaw", "goto"]):
        profile.update({"serving_weight": 280.0, "calories": 380, "protein_g": 15.0, "carbs_g": 45.0, "fat_g": 15.0})
    elif any(k in text for k in ["sinigang", "nilaga", "tinola", "bulalo", "papaitan", "kansi", "mami", "batchoy", "lomi", "sopas", "soup"]):
        profile.update({"serving_weight": 300.0, "calories": 220, "protein_g": 18.0, "carbs_g": 10.0, "fat_g": 12.0, "vitamin_c_mg": 8.0})
    elif any(k in text for k in ["lechon", "crispy pata", "chicharon", "bagnet", "sisig", "liempo", "humba"]):
        profile.update({"serving_weight": 150.0, "calories": 390, "protein_g": 22.0, "carbs_g": 4.0, "fat_g": 31.0})
    elif any(k in text for k in ["baboy", "pork", "menudo", "afritada", "igado", "bopis", "dinuguan", "embutido", "longganisa", "tocino"]):
        profile.update({"serving_weight": 200.0, "calories": 280, "protein_g": 19.0, "carbs_g": 9.0, "fat_g": 18.0})
    elif any(k in text for k in ["baka", "beef", "kaldereta", "caldereta", "mechado", "bistek", "pares", "tapa"]):
        profile.update({"serving_weight": 220.0, "calories": 290, "protein_g": 24.0, "carbs_g": 10.0, "fat_g": 17.0, "iron_mg": 2.8})
    elif any(k in text for k in ["manok", "chicken", "inasal", "curry"]):
        profile.update({"serving_weight": 200.0, "calories": 240, "protein_g": 25.0, "carbs_g": 6.0, "fat_g": 13.0})
    elif any(k in text for k in ["bangus", "tilapia", "isda", "fish", "paksiw", "escabeche", "relleno", "tinapa", "tuyo", "daing"]):
        profile.update({"serving_weight": 180.0, "calories": 210, "protein_g": 22.0, "carbs_g": 4.0, "fat_g": 11.0, "calcium_mg": 65.0})
    elif any(k in text for k in ["hipon", "shrimp", "pusit", "squid", "tahong", "alimango", "crab", "seafood", "kinilaw"]):
        profile.update({"serving_weight": 160.0, "calories": 165, "protein_g": 21.0, "carbs_g": 5.0, "fat_g": 6.0, "calcium_mg": 70.0})
    elif any(k in text for k in ["gulay", "pinakbet", "pakbet", "laing", "chopsuey", "chop suey", "ginisang", "ensalada", "lumpiang ubod", "monggo", "munggo"]):
        profile.update({"serving_weight": 200.0, "calories": 145, "protein_g": 6.0, "carbs_g": 14.0, "fat_g": 7.0, "vitamin_c_mg": 18.0, "calcium_mg": 55.0})
    elif any(k in text for k in ["pancit", "pansit", "bihon", "canton", "palabok", "malabon", "spaghetti"]):
        profile.update({"serving_weight": 220.0, "calories": 260, "protein_g": 10.0, "carbs_g": 36.0, "fat_g": 8.0})
    elif any(k in text for k in ["halo", "leche", "bibingka", "puto", "kutsinta", "suman", "sapin", "biko", "cassava", "maja", "turon", "banana", "camote", "carioca", "taho", "ube", "float", "buko"]):
        profile.update({"serving_weight": 120.0, "calories": 220, "protein_g": 3.5, "carbs_g": 38.0, "fat_g": 6.5})
    elif any(k in text for k in ["pandesal", "bread", "ensaymada", "pan de", "hopia", "monay", "mamon"]):
        profile.update({"serving_weight": 70.0, "calories": 215, "protein_g": 4.5, "carbs_g": 35.0, "fat_g": 6.5})
    elif any(k in text for k in ["kwek", "fishball", "kikiam", "isaw", "betamax", "adidas", "proben", "calamares", "ukoy", "empanada", "siomai", "siopao", "lumpia"]):
        profile.update({"serving_weight": 120.0, "calories": 230, "protein_g": 11.0, "carbs_g": 22.0, "fat_g": 11.0})

    return {
        "name": display_name,
        "synonyms": sorted(list({clean_key, display_name.lower()})),
        **profile,
    }


def _extract_mg(nutriments: Dict[str, Any], key: str) -> float:
    """
    Converts an OpenFoodFacts nutriment value per 100g into milligrams (mg).
    OpenFoodFacts stores standard nutriments in grams (g) per 100g unless unit is specified.
    """
    raw_val = nutriments.get(f"{key}_100g")
    if raw_val is None:
        return 0.0
    try:
        val = float(raw_val)
    except (ValueError, TypeError):
        return 0.0

    unit = str(nutriments.get(f"{key}_unit", "g")).lower().strip()
    if unit == "mg":
        return round(val, 1)
    if unit in ("ug", "µg", "mcg"):
        return round(val / 1000.0, 2)
    # Default unit in OpenFoodFacts nutriments_100g is grams ('g')
    return round(val * 1000.0, 1)


def _fetch_openfoodfacts_nutrition(clean_key: str, display_name: str) -> Optional[Dict[str, Any]]:
    """
    Queries the public OpenFoodFacts API (no API key required) for per-100g nutritional macros.
    Returns None if no matching product with valid calorie data is found or if offline.
    """
    try:
        res = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": clean_key,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
                "fields": "product_name,nutriments,serving_quantity",
            },
            headers={"User-Agent": "NutriAI/1.0 (Local Food Classifier Sync)"},
            timeout=5,
        )
        if res.status_code != 200:
            return None

        products = res.json().get("products") or []
        for product in products:
            nutr = product.get("nutriments") or {}
            kcal = nutr.get("energy-kcal_100g")
            if kcal is None and nutr.get("energy_100g") is not None:
                try:
                    kcal = float(nutr["energy_100g"]) / 4.184
                except (ValueError, TypeError):
                    kcal = None

            if kcal is None:
                continue

            try:
                calories = int(round(float(kcal)))
            except (ValueError, TypeError):
                continue

            if calories <= 0:
                continue

            serving_weight = 200.0
            if product.get("serving_quantity"):
                try:
                    sq = float(product["serving_quantity"])
                    if 10.0 <= sq <= 1000.0:
                        serving_weight = round(sq, 1)
                except (ValueError, TypeError):
                    pass

            return {
                "name": display_name,
                "synonyms": sorted(list({clean_key, display_name.lower()})),
                "serving_weight": serving_weight,
                "calories": calories,
                "protein_g": round(float(nutr.get("proteins_100g") or 0.0), 1),
                "carbs_g": round(float(nutr.get("carbohydrates_100g") or 0.0), 1),
                "fat_g": round(float(nutr.get("fat_100g") or 0.0), 1),
                "vitamin_c_mg": _extract_mg(nutr, "vitamin-c"),
                "calcium_mg": _extract_mg(nutr, "calcium"),
                "iron_mg": _extract_mg(nutr, "iron"),
            }
        return None
    except Exception:
        return None


def sync_labels_to_common_foods(labels_source=None, common_foods_path: str = None) -> List[str]:
    """
    Ensures every label in `labels_source` (either a path to labels.json, a dict, or a list of class names)
    has a matching entry in `common_foods.py`. Any missing labels are automatically fetched via
    OpenFoodFacts (or estimated via Filipino food keywords if offline) and appended to `common_foods.py`.

    Returns the list of newly added food keys.
    """
    try:
        from component.common_foods import COMMON_FOODS
    except ImportError:
        from backend.component.common_foods import COMMON_FOODS

    if common_foods_path is None:
        common_foods_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common_foods.py")

    # Resolve class names from path, dict, or list
    if isinstance(labels_source, str):
        if not os.path.exists(labels_source):
            return []
        with open(labels_source, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_labels = list(data.values()) if isinstance(data, dict) else list(data)
    elif isinstance(labels_source, dict):
        raw_labels = list(labels_source.values())
    elif isinstance(labels_source, (list, tuple, set)):
        raw_labels = list(labels_source)
    else:
        return []

    # Build lookup set of all existing keys and synonyms
    existing_terms = set()
    for key, info in COMMON_FOODS.items():
        existing_terms.add(key.lower().strip())
        for syn in info.get("synonyms", []):
            existing_terms.add(syn.lower().strip())

    new_entries = {}
    for raw_label in raw_labels:
        clean_key = re.sub(r"[_-]+", " ", str(raw_label)).strip().lower()
        if not clean_key or clean_key in existing_terms:
            continue

        display_name = " ".join(w.capitalize() for w in clean_key.split())
        entry = _fetch_openfoodfacts_nutrition(clean_key, display_name)
        if not entry:
            entry = _estimate_nutrition_from_keywords(clean_key, display_name)

        new_entries[clean_key] = entry
        COMMON_FOODS[clean_key] = entry
        existing_terms.add(clean_key)

    if not new_entries:
        return []

    # Append new entries to common_foods.py before the closing brace
    with open(common_foods_path, "rb") as f:
        raw_bytes = f.read()
    line_ending = "\r\n" if b"\r\n" in raw_bytes else "\n"
    content = raw_bytes.decode("utf-8")

    rbrace_idx = content.rfind("}")
    if rbrace_idx == -1:
        return []

    before = content[:rbrace_idx].rstrip()
    if not before.endswith(","):
        before += ","

    formatted_blocks = []
    for key, entry in new_entries.items():
        entry_json = json.dumps(entry, indent=8)
        # Indent closing brace of entry to 4 spaces
        lines = entry_json.splitlines()
        if len(lines) > 1:
            lines[-1] = "    }"
        block = f'    "{key}": ' + line_ending.join(lines)
        formatted_blocks.append(block)

    updated_content = (
        before
        + line_ending
        + ("," + line_ending).join(formatted_blocks)
        + line_ending
        + "}"
        + line_ending
    )

    with open(common_foods_path, "wb") as f:
        f.write(updated_content.encode("utf-8"))

    print(f"Auto-synced {len(new_entries)} new food(s) into common_foods.py: {', '.join(new_entries.keys())}")
    return list(new_entries.keys())
