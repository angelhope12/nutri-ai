"""
=============================================================================
Food-101 Category to Nutrition Mapping Module
=============================================================================
Maps Kaggle Food-101 raw class names (e.g. 'caesar_salad', 'pad_thai', 'hamburger')
to human-readable names and standard macro profiles if local DB miss occurs.
"""

from typing import Dict, Any, Optional
from component.common_foods import COMMON_FOODS

# Standard estimated nutritional fallback values (per average serving) for common Food-101 categories
FOOD101_ESTIMATED_PROFILES: Dict[str, Dict[str, Any]] = {
    "pizza": {"calories": 285, "protein_g": 12.0, "carbs_g": 36.0, "fat_g": 10.0, "vitamin_c_mg": 1.2, "calcium_mg": 200.0, "iron_mg": 2.5},
    "hamburger": {"calories": 354, "protein_g": 20.0, "carbs_g": 29.0, "fat_g": 17.0, "vitamin_c_mg": 0.5, "calcium_mg": 100.0, "iron_mg": 3.0},
    "french_fries": {"calories": 312, "protein_g": 3.4, "carbs_g": 41.0, "fat_g": 15.0, "vitamin_c_mg": 4.5, "calcium_mg": 18.0, "iron_mg": 0.8},
    "sushi": {"calories": 200, "protein_g": 9.0, "carbs_g": 38.0, "fat_g": 1.5, "vitamin_c_mg": 0.0, "calcium_mg": 20.0, "iron_mg": 1.2},
    "caesar_salad": {"calories": 190, "protein_g": 7.0, "carbs_g": 8.0, "fat_g": 15.0, "vitamin_c_mg": 18.0, "calcium_mg": 150.0, "iron_mg": 1.5},
    "pad_thai": {"calories": 380, "protein_g": 14.0, "carbs_g": 52.0, "fat_g": 13.0, "vitamin_c_mg": 6.0, "calcium_mg": 40.0, "iron_mg": 2.0},
    "ramen": {"calories": 436, "protein_g": 10.0, "carbs_g": 56.0, "fat_g": 18.0, "vitamin_c_mg": 0.0, "calcium_mg": 30.0, "iron_mg": 2.2},
    "tacos": {"calories": 226, "protein_g": 12.0, "carbs_g": 20.0, "fat_g": 11.0, "vitamin_c_mg": 3.0, "calcium_mg": 90.0, "iron_mg": 1.8},
    "fried_rice": {"calories": 238, "protein_g": 5.5, "carbs_g": 45.0, "fat_g": 4.1, "vitamin_c_mg": 1.0, "calcium_mg": 23.0, "iron_mg": 1.1},
    "spaghetti_marinara": {"calories": 310, "protein_g": 11.0, "carbs_g": 55.0, "fat_g": 5.0, "vitamin_c_mg": 12.0, "calcium_mg": 45.0, "iron_mg": 2.4},
    "steak": {"calories": 271, "protein_g": 26.0, "carbs_g": 0.0, "fat_g": 18.0, "vitamin_c_mg": 0.0, "calcium_mg": 18.0, "iron_mg": 2.9},
    "chicken_wings": {"calories": 290, "protein_g": 27.0, "carbs_g": 0.0, "fat_g": 19.0, "vitamin_c_mg": 0.0, "calcium_mg": 15.0, "iron_mg": 1.3},
    "donuts": {"calories": 269, "protein_g": 4.0, "carbs_g": 31.0, "fat_g": 15.0, "vitamin_c_mg": 0.2, "calcium_mg": 35.0, "iron_mg": 1.4},
    "ice_cream": {"calories": 207, "protein_g": 3.5, "carbs_g": 24.0, "fat_g": 11.0, "vitamin_c_mg": 0.6, "calcium_mg": 128.0, "iron_mg": 0.2},
    "pancakes": {"calories": 227, "protein_g": 6.0, "carbs_g": 28.0, "fat_g": 10.0, "vitamin_c_mg": 0.0, "calcium_mg": 160.0, "iron_mg": 1.8},
}

def format_class_name(raw_name: str) -> str:
    """
    Converts raw snake_case or hyphenated class name to readable Title Case.
    Example: 'caesar_salad' -> 'Caesar Salad'
    """
    cleaned = raw_name.replace("_", " ").replace("-", " ").strip()
    return cleaned.title()

def get_nutrition_for_class(raw_class_name: str) -> Dict[str, Any]:
    """
    Attempts to map raw predicted class name to local COMMON_FOODS DB first,
    then to static estimated profiles, and defaults to standard baseline values.
    """
    display_name = format_class_name(raw_class_name)
    query_key = raw_class_name.lower().replace("_", " ").strip()

    # 1. Match against COMMON_FOODS dictionary
    for key, info in COMMON_FOODS.items():
        if query_key == key or query_key in info.get("synonyms", []):
            return {
                "food_name": info["name"],
                "calories": int(round(info["calories"])),
                "protein_g": float(info["protein_g"]),
                "carbs_g": float(info["carbs_g"]),
                "fat_g": float(info["fat_g"]),
                "vitamin_c_mg": float(info["vitamin_c_mg"]),
                "calcium_mg": float(info["calcium_mg"]),
                "iron_mg": float(info["iron_mg"]),
            }

    # 2. Check predefined static profile fallback
    if raw_class_name.lower() in FOOD101_ESTIMATED_PROFILES:
        profile = FOOD101_ESTIMATED_PROFILES[raw_class_name.lower()]
        return {
            "food_name": display_name,
            "calories": profile["calories"],
            "protein_g": profile["protein_g"],
            "carbs_g": profile["carbs_g"],
            "fat_g": profile["fat_g"],
            "vitamin_c_mg": profile["vitamin_c_mg"],
            "calcium_mg": profile["calcium_mg"],
            "iron_mg": profile["iron_mg"],
        }

    # 3. Default generalized baseline nutrition estimation
    return {
        "food_name": display_name,
        "calories": 250,
        "protein_g": 10.0,
        "carbs_g": 30.0,
        "fat_g": 10.0,
        "vitamin_c_mg": 5.0,
        "calcium_mg": 50.0,
        "iron_mg": 1.5,
    }
