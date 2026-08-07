"""
=============================================================================
NutriAI - Dynamic Food Addition & Retraining Pipeline
=============================================================================

This script allows you to add ANY new food category dynamically by passing its name.

Workflow:
1. Takes user input (e.g. "Lechon Baboy" or "Bicol Express").
2. Automatically scrapes images from Bing into `philippine_food_dataset/<category_label>/` if not already present.
3. Automatically retrains the PyTorch model and re-exports `food_classifier.onnx` & `labels.json`.

Usage:
  python3 backend/add_new_food.py "Lechon Baboy" --images 60 --epochs 3
"""

import os
import sys
import re
import json
import argparse
import subprocess

def clean_food_key(food_name: str) -> str:
    """
    Converts user input like 'Lechon Baboy!' or 'Kare-Kare' into 'lechon_baboy' or 'kare_kare'.
    """
    cleaned = re.sub(r'[^a-zA-Z0-9]', '_', food_name.strip().lower())
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned

def scrape_food_images(food_name: str, folder_name: str, dataset_dir: str, images_per_class: int):
    """
    Scrapes Bing images for a newly added food item if the folder doesn't exist or is empty.
    """
    target_folder = os.path.join(dataset_dir, folder_name)
    os.makedirs(target_folder, exist_ok=True)
    
    existing_images = [f for f in os.listdir(target_folder) if not f.startswith(".")]
    if len(existing_images) >= images_per_class:
        print(f"Skipping scraping: '{folder_name}' already contains {len(existing_images)} images.")
        return

    print(f"\n[Step 1/3] Automatically scraping images for user input: '{food_name}'...")
    query = f"{food_name} filipino food dish"
    
    try:
        from icrawler.builtin import BingImageCrawler
        bing_crawler = BingImageCrawler(
            downloader_threads=4,
            storage={'root_dir': target_folder}
        )
        bing_crawler.crawl(
            keyword=query,
            filters=None,
            max_num=images_per_class,
            min_size=(200, 200),
            file_idx_offset=0
        )
        print(f"Successfully scraped images for '{food_name}' into '{target_folder}'.")
    except Exception as e:
        print(f"Error during image scraping: {e}")

def retrain_model(dataset_dir: str, epochs: int, onnx_out: str, labels_out: str):
    """
    Retrains MobileNetV3-Large on dataset_dir (including newly added food folders) and exports ONNX.
    """
    print(f"\n[Step 2/3] Retraining model with updated dataset (including new food)...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_script = os.path.join(base_dir, "train_local_model.py")
    
    cmd = [
        sys.executable, train_script,
        "--dataset_dir", dataset_dir,
        "--epochs", str(epochs),
        "--onnx_out", onnx_out,
        "--labels_out", labels_out
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print("\n[Step 3/3] Retraining & ONNX export complete!")

def add_new_food_pipeline(food_name: str, dataset_dir: str, images_per_class: int, epochs: int):
    folder_name = clean_food_key(food_name)
    print("=" * 60)
    print(f"NutriAI - Adding New Food: '{food_name}'")
    print(f"Category Label: '{folder_name}'")
    print("=" * 60)
    
    # 1. Scrape images if not already existing
    scrape_food_images(food_name, folder_name, dataset_dir, images_per_class)
    
    # 2. Retrain model & export updated ONNX + labels.json
    base_dir = os.path.dirname(os.path.abspath(__file__))
    onnx_out = os.path.join(base_dir, "models", "food_classifier.onnx")
    labels_out = os.path.join(base_dir, "models", "labels.json")
    
    retrain_model(dataset_dir, epochs, onnx_out, labels_out)
    
    print("=" * 60)
    print(f"Successfully added '{food_name}' to trained model!")
    print(f"Model File: {onnx_out}")
    print(f"Labels File: {labels_out}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Add a new food item dynamically to training dataset and retrain model")
    parser.add_argument("food_name", type=str, help="Name of the food to add (e.g. 'Lechon Baboy')")
    parser.add_argument("--dataset_dir", type=str, default="philippine_food_dataset", help="Dataset directory path")
    parser.add_argument("--images", type=int, default=60, help="Number of images to scrape if not existing")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    
    args = parser.parse_args()
    add_new_food_pipeline(args.food_name, args.dataset_dir, args.images, args.epochs)

if __name__ == "__main__":
    main()
