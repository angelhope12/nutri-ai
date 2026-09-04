"""
=============================================================================
NutriAI - Philippine Food Dataset Scraper
=============================================================================

This script automatically downloads image datasets for common Philippine foods
and organizes them into standard PyTorch ImageFolder layout:

    philippine_food_dataset/
      ├── adobong_baboy/
      ├── pork_sinigang/
      ├── halo_halo/
      └── ...

You can feed the output directory directly into `backend/train_local_model.py`.
"""

import os
import sys
import time
import argparse

try:
    from icrawler.builtin import BingImageCrawler
except ImportError:
    print("Error: 'icrawler' package is not installed.")
    print("Please install it using: python3 -m pip install icrawler pillow")
    sys.exit(1)

# Catalog of Philippine Foods mapped to image search queries
PHILIPPINE_FOOD_CATALOG = {
    # Pork & Beef
    "lechon_baboy": "lechon baboy roast pig filipino dish",
    "adobong_baboy": "pork adobo filipino food dish",
    "pork_sinigang": "sinigang na baboy soup filipino",
    "kare_kare": "kare kare peanut stew filipino dish",
    "crispy_pata": "crispy pata deep fried pork leg filipino",
    "pork_sisig": "sizzling pork sisig filipino",
    "bicol_express": "bicol express spicy pork coconut filipino",
    "lechon_kawali": "lechon kawali crispy pork belly filipino",
    "pork_menudo": "pork menudo stew filipino",
    "dinuguan": "dinuguan pork blood stew filipino",
    "bulalo": "beef bulalo bone marrow soup filipino",
    "beef_caldereta": "beef caldereta tomato stew filipino",
    "bistek_tagalog": "bistek tagalog beef steak onion filipino",
    "beef_pares": "beef pares stew with garlic rice filipino",
    "pork_tocino": "pork tocino sweet cured pork filipino",
    "lumpia_shanghai": "lumpiang shanghai pork spring roll filipino",

    # Chicken & Poultry
    "chicken_adobo": "chicken adobo dish filipino",
    "chicken_inasal": "chicken inasal grilled chicken bacolod filipino",
    "chicken_tinola": "chicken tinola ginger soup papaya filipino",
    "chicken_afritada": "chicken afritada stew filipino",
    "chicken_curry_pinoy": "filipino chicken curry yellow",
    "arroz_caldo": "arroz caldo chicken rice porridge filipino",
    "chicken_sopas": "chicken sopas macaroni soup filipino",
    
    # Seafood
    "sinigang_na_bangus": "sinigang na bangus milkfish soup filipino",
    "sinigang_na_hipon": "sinigang na hipon shrimp soup filipino",
    "inihaw_na_tilapia": "inihaw na tilapia grilled fish filipino",
    "inihaw_na_bangus": "inihaw na bangus stuffed milkfish filipino",
    "adobong_pusit": "adobong pusit squid ink stew filipino",
    "kinilaw_na_tanigue": "kinilaw na tanigue raw fish ceviche filipino",
    "tortang_talong": "tortang talong eggplant omelet filipino",
    "daing_na_bangus": "daing na bangus fried marinated milkfish filipino",
    "tuyo_dried_fish": "tuyo dried fish salted filipino",

    # Vegetables & Tofu
    "pinakbet": "pinakbet vegetables bagoong filipino",
    "laing": "laing taro leaves coconut milk filipino",
    "gising_gising": "gising gising green beans coconut filipino",
    "chopsuey_pinoy": "chopsuey filipino style stir fry vegetables",
    "lumpiang_sariwa": "lumpiang sariwa fresh spring roll filipino",
    "tokwat_baboy": "tokwat baboy tofu pork vinegar filipino",

    # Rice & Silog
    "tapsilog": "tapsilog beef tapa egg garlic rice filipino",
    "tocilog": "tocilog pork tocino egg garlic rice filipino",
    "longsilog": "longsilog sausage egg garlic rice filipino",
    "bangsilog": "bangsilog bangus egg garlic rice filipino",
    "sinangag": "sinangag garlic fried rice filipino",
    
    # Noodles & Pastas
    "pancit_canton": "pancit canton stir fried noodles filipino",
    "pancit_bihon": "pancit bihon rice noodles filipino",
    "pancit_palabok": "pancit palabok orange sauce shrimp noodles filipino",
    "pancit_malabon": "pancit malabon thick seafood noodles filipino",
    "lomi_batangas": "lomi batangas thick noodle soup filipino",
    "filipino_spaghetti": "sweet filipino spaghetti hotdog cheese",
    "la_paz_batchoy": "la paz batchoy noodle soup iloilo filipino",

    # Street Foods & Finger Foods
    "kwek_kwek": "kwek kwek orange quail eggs street food filipino",
    "isaw_bbq": "isaw grilled chicken intestines street food filipino",
    "balut": "balut duck egg street food filipino",
    "taho": "taho warm tofu arnibal sago filipino",
    "turon": "turon banana lumpia caramel filipino",
    "banana_cue": "banana cue sugar fried saba filipino",
    "chicharon_bulaklak": "chicharon bulaklak fried pork mesentery filipino",

    # Desserts & Kakanin
    "halo_halo": "halo halo shaved ice dessert filipino",
    "leche_flan": "leche flan caramel custard filipino",
    "bibingka": "bibingka rice cake salted egg coconut filipino",
    "puto_bumbong": "puto bumbong purple sticky rice bamboo filipino",
    "ube_halaya": "ube halaya purple yam jam filipino",
    "biko": "biko sticky rice brown sugar latik filipino",
    "sapin_sapin": "sapin sapin layered rice cake filipino",
    "cassava_cake": "cassava cake baked coconut filipino",
    "mango_float": "mango float graham cake filipino",
    "buko_pandan": "buko pandan salad jelly coconut filipino",

    # Breads & Bakery
    "pandesal": "pandesal bread rolls filipino",
    "spanish_bread": "spanish bread sweet butter filling filipino",
    "ensaymada": "ensaymada brioche cheese sugar filipino",
    "pan_de_coco": "pan de coco coconut bread filipino",
    "hopia": "hopia pastry ube mongo filipino"
}

def download_philippine_food_dataset(dataset_dir: str, images_per_class: int):
    """
    Downloads images for each Philippine food class into PyTorch ImageFolder layout.
    """
    os.makedirs(dataset_dir, exist_ok=True)
    total_classes = len(PHILIPPINE_FOOD_CATALOG)
    
    print("=" * 60)
    print("NutriAI - Philippine Food Dataset Scraper")
    print(f"Total Food Categories: {total_classes}")
    print(f"Target Images per Category: {images_per_class}")
    print(f"Output Directory: {os.path.abspath(dataset_dir)}")
    print("=" * 60 + "\n")

    for idx, (folder_name, query) in enumerate(PHILIPPINE_FOOD_CATALOG.items(), 1):
        target_folder = os.path.join(dataset_dir, folder_name)
        
        # Skip downloading if folder already exists and has enough images
        if os.path.exists(target_folder):
            existing_count = len([f for f in os.listdir(target_folder) if not f.startswith(".")])
            if existing_count >= images_per_class:
                print(f"[{idx}/{total_classes}] Skipping '{folder_name}' ({existing_count} images already present).")
                continue

        print(f"[{idx}/{total_classes}] Crawling images for '{folder_name}' (Query: '{query}')...")
        
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
        
        time.sleep(0.5)

    print("\nDataset scraping successfully completed!")
    print(f"Images saved in: {os.path.abspath(dataset_dir)}")

def main():
    parser = argparse.ArgumentParser(description="Download Philippine Food Images for ML Training")
    parser.add_argument("--dataset_dir", type=str, default="philippine_food_dataset", help="Output directory path")
    parser.add_argument("--limit", type=int, default=100, help="Number of images per category")
    
    args = parser.parse_args()
    download_philippine_food_dataset(args.dataset_dir, args.limit)

if __name__ == "__main__":
    main()
