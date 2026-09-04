### Pre-requisites
- Python 3.11
- PostgreSQL
- Vercel CLI

run: 
1. `powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1`
2. Set postgres path: (open command prompt as admin)
    - `setx PATH "%PATH%;C:\Program Files\PostgreSQL\17\bin"`
3. Open C:\Program Files\PostgreSQL\17\data\pg_hba.conf in Notepad (Run as Administrator)
    Find lines like:

    host    all             all             127.0.0.1/32            md5
    host    all             all             ::1/128                 md5

    Change md5 → trust
4. Initialize the local database: 
    - `psql -U postgres -c "CREATE DATABASE nutriai_db;"` (hit Enter if asked for password, ensuring it remains empty)
5. `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## How to run locally (2 separate terminals)
frontend
- cd frontend
- ..\venv\Scripts\python.exe -m http.server 3000

backend
- cd backend
- ..\venv\Scripts\activate; python main.py

## How to Train the Model on Another Device

To train or retrain the MobileNetV3 food classifier model after cloning this repository on a new machine:

### 1. Install Machine Learning Dependencies
Install the required ML training stack:
```bash
pip install torch torchvision pillow icrawler tqdm onnxruntime
```

### 2. Download or Scrape the Dataset
Raw image datasets are omitted from Git. Automatically scrape Philippine food images into `philippine_food_dataset/`:
```bash
python backend/scrape_philippine_foods.py --dataset_dir philippine_food_dataset --limit 100
```

### 3. Train & Export ONNX Model
Run `train_local_model.py` to fine-tune the model and export `food_classifier.onnx` and `labels.json`:
```bash
python backend/train_local_model.py --dataset_dir philippine_food_dataset --epochs 5 --onnx_out backend/models/food_classifier.onnx --labels_out backend/models/labels.json
```

#### Shortcut: Adding & Retraining a New Food Item
To add a single new food category dynamically and retrain:
```bash
python backend/add_new_food.py "Pork Sisig" --images 60 --epochs 3
```

### 4. (Optional) Test the Trained Model
```bash
python test_local_model.py --image path/to/sample_food_image.jpg
```