"""
=============================================================================
NutriAI - Dataset Splitter Utility (Train / Validation Split)
=============================================================================

Splits images from `pending_review/` (or single-folder class layout) into:
    dataset_dir/
      ├── train/
      │     ├── class_a/
      │     └── class_b/
      └── val/
            ├── class_a/
            └── class_b/
"""

import os
import sys
import shutil
import random
import argparse

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def is_valid_image(filename: str) -> bool:
    if filename.startswith(".") or filename.startswith("._") or "__MACOSX" in filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in VALID_EXTENSIONS

def split_dataset(dataset_dir: str, split_ratio: float = 0.8, seed: int = 42, only_missing: bool = False):
    random.seed(seed)
    
    # Check source folder: check pending_review first, otherwise dataset_dir itself
    pending_dir = os.path.join(dataset_dir, "pending_review")
    source_dir = pending_dir if os.path.isdir(pending_dir) else dataset_dir

    train_dir = os.path.join(dataset_dir, "train")
    val_dir = os.path.join(dataset_dir, "val")

    # Find category folders
    class_dirs = [
        d for d in os.listdir(source_dir)
        if os.path.isdir(os.path.join(source_dir, d)) and d not in {"train", "val", "pending_review", "__MACOSX"} and not d.startswith(".")
    ]

    if not class_dirs:
        print(f"Error: No category folders found in '{source_dir}'.")
        sys.exit(1)

    print("=" * 60)
    print("NutriAI - Dataset Train/Validation Splitter")
    print(f"Source Directory: {os.path.abspath(source_dir)}")
    print(f"Output: {os.path.abspath(train_dir)} ({int(split_ratio*100)}%) | {os.path.abspath(val_dir)} ({int((1-split_ratio)*100)}%)")
    print(f"Found {len(class_dirs)} food categories.")
    print("=" * 60 + "\n")

    total_train = 0
    total_val = 0
    synced_count = 0

    for idx, class_name in enumerate(sorted(class_dirs), 1):
        target_train = os.path.join(train_dir, class_name)
        target_val = os.path.join(val_dir, class_name)

        if only_missing and os.path.isdir(target_train) and os.path.isdir(target_val):
            existing_train = [f for f in os.listdir(target_train) if is_valid_image(f)]
            existing_val = [f for f in os.listdir(target_val) if is_valid_image(f)]
            if existing_train and existing_val:
                continue

        class_src = os.path.join(source_dir, class_name)
        images = [f for f in os.listdir(class_src) if is_valid_image(f)]
        random.shuffle(images)

        if not images:
            continue

        split_point = max(1, int(len(images) * split_ratio))
        train_images = images[:split_point]
        val_images = images[split_point:]

        # Create target directories
        os.makedirs(target_train, exist_ok=True)
        os.makedirs(target_val, exist_ok=True)

        for img in train_images:
            shutil.copy2(os.path.join(class_src, img), os.path.join(target_train, img))
        for img in val_images:
            shutil.copy2(os.path.join(class_src, img), os.path.join(target_val, img))

        total_train += len(train_images)
        total_val += len(val_images)
        synced_count += 1
        print(f"[{idx}/{len(class_dirs)}] {class_name}: {len(train_images)} train, {len(val_images)} val")

    print("\n" + "=" * 60)
    print("Dataset Split Complete!")
    print(f"Categories Processed: {synced_count} (Total Categories: {len(class_dirs)})")
    print(f"Train Images Copied: {total_train}")
    print(f"Validation Images Copied: {total_val}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Split dataset into train/ and val/ sets")
    parser.add_argument("--dataset_dir", type=str, default="philippine_food_dataset", help="Dataset directory")
    parser.add_argument("--split_ratio", type=float, default=0.8, help="Train split ratio (default: 0.8)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    split_dataset(args.dataset_dir, args.split_ratio, args.seed)

if __name__ == "__main__":
    main()
