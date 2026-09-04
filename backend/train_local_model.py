"""
=============================================================================
NutriAI - Local Food Classifier Training & ONNX Export Script (MobileNetV3-Large)
=============================================================================

This script fine-tunes a MobileNetV3-Large model on the Kaggle Food-101 dataset
(or any image classification dataset organized in standard image folders)
and exports the trained model to ONNX format for ultra-fast, lightweight CPU inference in FastAPI.

HOW TO RUN ON KAGGLE (Free T4 GPU):
----------------------------------
1. Create a new Kaggle Notebook at https://www.kaggle.com
2. Enable GPU Accelerator (P100 or T4 x2) in Notebook Settings.
3. Add the dataset: Search for "dansbecker/food-101" or "food-101".
4. Copy and paste this script into a Kaggle code cell and run it.
5. Download the output files:
   - `food_classifier.onnx`
   - `labels.json`
6. Place `food_classifier.onnx` and `labels.json` into `nutri-ai/backend/models/`.

HOW TO RUN LOCALLY:
-------------------
`python backend/train_local_model.py --dataset_dir /path/to/food-101/images --epochs 5`
"""

import os
import json
import argparse
import time
from typing import Tuple

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

def is_valid_image_file(path: str) -> bool:
    """
    Filters out macOS metadata files (e.g. ._filename.jpg, __MACOSX) and non-image files.
    """
    filename = os.path.basename(path)
    if filename.startswith(".") or filename.startswith("._") or "__MACOSX" in path:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

def get_data_loaders(data_dir: str, batch_size: int = 32, num_workers: int = 4) -> Tuple[DataLoader, DataLoader, list]:
    """
    Sets up PyTorch DataLoaders with ImageNet augmentations & normalization.
    """
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # If dataset has train/val subdirectories
    train_dir = os.path.join(data_dir, 'train') if os.path.exists(os.path.join(data_dir, 'train')) else data_dir
    val_dir = os.path.join(data_dir, 'val') if os.path.exists(os.path.join(data_dir, 'val')) else train_dir

    train_dataset = datasets.ImageFolder(root=train_dir, transform=train_transform, is_valid_file=is_valid_image_file)
    val_dataset = datasets.ImageFolder(root=val_dir, transform=val_transform, is_valid_file=is_valid_image_file)

    class_names = train_dataset.classes
    print(f"Loaded dataset from '{data_dir}'. Found {len(class_names)} food categories.")

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    return train_loader, val_loader, class_names


def build_mobilenet_v3_large(num_classes: int) -> nn.Module:
    """
    Instantiates a pre-trained MobileNetV3-Large backbone and replaces the final classifier head.
    """
    print("Loading pre-trained MobileNetV3-Large backbone...")
    model = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.DEFAULT)

    # Freeze feature extractor layers initially to speed up training
    for param in model.features.parameters():
        param.requires_grad = False

    # Replace classifier head for target food categories
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)

    return model


def train_model(model: nn.Module, train_loader: DataLoader, val_loader: DataLoader, epochs: int, device: torch.device):
    """
    Trains the classifier head and unfreezes top layers for fine-tuning.
    """
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    model.to(device)
    print(f"Starting training on device: {device}")

    for epoch in range(epochs):
        start_time = time.time()
        
        # --- Training ---
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct_train += torch.sum(preds == labels.data).item()
            total_train += labels.size(0)

        scheduler.step()
        epoch_loss = running_loss / total_train
        epoch_acc = (correct_train / total_train) * 100.0

        # --- Validation ---
        model.eval()
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_acc = (val_correct / val_total) * 100.0 if val_total > 0 else 0.0
        elapsed = time.time() - start_time

        print(f"Epoch [{epoch+1}/{epochs}] ({elapsed:.1f}s) - Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.2f}% | Val Acc: {val_acc:.2f}%")

    print("Training finished!")
    return model


def export_to_onnx(model: nn.Module, class_names: list, output_onnx_path: str, output_json_path: str):
    """
    Exports the trained PyTorch model to ONNX format and writes labels.json.
    """
    model.eval()
    model.to("cpu")

    # Create dummy tensor matching standard input batch size (1, 3, 224, 224)
    dummy_input = torch.randn(1, 3, 224, 224)

    os.makedirs(os.path.dirname(os.path.abspath(output_onnx_path)), exist_ok=True)

    print(f"Exporting model to ONNX: {output_onnx_path}")
    torch.onnx.export(
        model,
        dummy_input,
        output_onnx_path,
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )
    print("ONNX export complete!")

    # Save class label mapping dict
    labels_dict = {i: name for i, name in enumerate(class_names)}
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(labels_dict, f, indent=2)

    print(f"Class labels saved to: {output_json_path}")


def find_kaggle_food_dataset() -> str:
    """
    Recursively scans /kaggle/input to find the REAL image directory containing 101 food class subdirectories,
    strictly ignoring macOS metadata __MACOSX folders.
    """
    base_input = "/kaggle/input"
    if os.path.exists(base_input):
        for root, dirs, files in os.walk(base_input):
            # Ignore macOS metadata directories
            if "__MACOSX" in root:
                continue
            # Check if this directory directly contains food class folders
            if "apple_pie" in dirs and "pizza" in dirs and "sushi" in dirs:
                return root
    return None

def main(dataset_dir: str = None, epochs: int = None):
    parser = argparse.ArgumentParser(description="Train MobileNetV3-Large Food Classifier & Export to ONNX")
    parser.add_argument("--dataset_dir", type=str, default="food-101/images", help="Path to food images dataset directory")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--onnx_out", type=str, default="food_classifier.onnx", help="Output path for ONNX model")
    parser.add_argument("--labels_out", type=str, default="labels.json", help="Output path for labels.json")
    
    # Use parse_known_args to ignore Jupyter kernel `-f` arguments
    args, _ = parser.parse_known_args()

    target_dataset_dir = dataset_dir or args.dataset_dir
    target_epochs = epochs or args.epochs

    # Dynamic auto-detection of Kaggle dataset path
    if not os.path.exists(target_dataset_dir):
        detected_path = find_kaggle_food_dataset()
        if detected_path:
            print(f"Auto-detected Kaggle food dataset at: '{detected_path}'")
            target_dataset_dir = detected_path

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.exists(target_dataset_dir):
        print(f"Error: Dataset directory '{target_dataset_dir}' not found.")
        print("Please ensure the Kaggle food-101 dataset is added to your notebook.")
        return

    train_loader, val_loader, class_names = get_data_loaders(target_dataset_dir, batch_size=args.batch_size)
    model = build_mobilenet_v3_large(num_classes=len(class_names))
    model = train_model(model, train_loader, val_loader, epochs=target_epochs, device=device)

    export_to_onnx(model, class_names, args.onnx_out, args.labels_out)


if __name__ == "__main__":
    main()
