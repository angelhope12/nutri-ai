# Food recognition training — next stage

Training is separate from interface development. Finish and test the code revision first. Then prepare reviewed images, train and measure the classifier, add the accepted model and matching labels to GitHub, test the integrated app, and merge to master for production. Do not train inside Vercel.

## 1 Choose and label foods
Start with a manageable list of foods you actually want to recognize. Each image needs one correct class. Use your own photos or images licensed for this purpose, with varied plates, lighting, camera angles and backgrounds. Do not add unrelated photos or screenshots containing search results. Similar dishes and mixed plates need explicit labeling rules.

The reviewed archive contains 479 food candidates, 382 items needing label review, and 1,383 excluded/unsuitable files. None of these buckets is automatically approved training data. Inspect each candidate before copying it into the approved dataset. Do not move quarantine folders directly into training. A food classifier trained only on foods can still force a non-food photo into a food class; test non-food inputs separately and add an explicit rejection design before claiming food/non-food detection.

## 2 Organize independently reviewed images
Create these folders on the training computer (not GitHub/Vercel):

```
approved_foods/
  train/
    chicken_adobo/
    sinigang/
  val/
    chicken_adobo/
    sinigang/
  test/
    chicken_adobo/
    sinigang/
```

Put the corresponding JPG/PNG photos inside each class folder. Every split must contain the same classes. Keep all photos of the same dish/photo shoot/source sequence in ONE split; never put copies, crops or near-duplicates across splits. Roughly 70/15/15 is a starting allocation, not a guarantee of adequate data. Reserve test images before training and do not tune on them. Keep a manifest with filename, class, source/permission and split. Class names must map to the nutrition database; adding an image folder alone does not add verified nutrition values or allergy ingredients.

## 3 Prepare a separate training environment
Use a GPU-equipped training computer or a hosted GPU notebook. Use PyTorch's official installer for the machine's OS/CUDA version: https://pytorch.org/get-started/locally/. Training needs torch, torchvision, Pillow, numpy and ONNX export dependencies; do not add the large training stack to the Vercel runtime requirements. Select the exact installation commands after confirming the training hardware.

The current script is backend/train_local_model.py. Once the environment and reviewed dataset are ready, run from the app root:

```
python backend/train_local_model.py --dataset_dir approved_foods --epochs 10 --batch_size 32 --onnx_out training_output/food_classifier.onnx --labels_out training_output/labels.json
```

This is a starting experiment, not a promised accuracy target. Training uses ImageNet initialization and downloads those weights the first time. The current script trains the classifier head and prints validation accuracy per epoch. Its output must be evaluated before replacing the existing model. More epochs cannot fix mislabeled images.

## 4 Evaluate before accepting
Measure per-class precision/recall and confusion on the untouched test set, along with non-food rejection, low-confidence handling, real camera images and ONNX/PyTorch prediction agreement. Inspect failures, not just overall accuracy. Select confidence thresholds using validation data, then report final test results separately. Images do not provide exact portions, recipe ingredients or verified nutrients; these require separate data and validation.

## 5 Integrate the accepted model
Only after evaluation, copy BOTH food_classifier.onnx and its matching labels.json to backend/models/. Keep the previous model backup. Update MODEL_STATUS.md with dataset provenance, split counts, metrics and limitations. Upload the pair through the same test branch, verify real food inference on Vercel, then merge the completed changes into master.

No new training has been run for revision 2. We first need the approved classes/images and the chosen training hardware to carry out the training stage honestly.
