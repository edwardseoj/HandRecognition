# process_kaggle_dataset_rename.py

import os
import csv
import cv2
import mediapipe as mp

# -------------------------------
# CONFIGURATION
# -------------------------------
DATA_DIR = "gesture_data/HaGRID"       # Path to manually downloaded Kaggle dataset
OUTPUT_CSV = "gesture_data/hand_gestures.csv"
TARGET_SAMPLES_PER_LABEL = None        # None = process all images

# -------------------------------
# STEP 1: Prepare CSV
# -------------------------------
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "w", newline="") as f:
        header = ["label"] + [f"{c}{i}" for i in range(21) for c in ("x","y","z")]
        csv.writer(f).writerow(header)
    print(f"✅ Created CSV: {OUTPUT_CSV}")

# -------------------------------
# STEP 2: Initialize MediaPipe
# -------------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# -------------------------------
# STEP 3: Ask user to rename labels
# -------------------------------
folders = [f for f in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, f))]
label_map = {}

print("📂 Found the following labels:")
for i, folder in enumerate(folders):
    print(f"{i+1}. {folder}")

print("\n✏️ You can now rename each label (press Enter to keep the original name).")
for folder in folders:
    new_name = input(f"Rename '{folder}' -> ").strip()
    if not new_name:
        new_name = folder
    label_map[folder] = new_name

print("\n✅ Label renaming complete:")
for orig, new in label_map.items():
    print(f"{orig} -> {new}")

# -------------------------------
# STEP 4: Count total images for progress
# -------------------------------
total_images = 0
for folder in folders:
    folder_path = os.path.join(DATA_DIR, folder)
    total_images += len([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg','.png'))])

print(f"\n🖼 Total images to process: {total_images}")

# -------------------------------
# STEP 5: Process images and save CSV
# -------------------------------
processed_images = 0
with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
    for folder in folders:
        folder_path = os.path.join(DATA_DIR, folder)
        count = 0

        for img_file in os.listdir(folder_path):
            if TARGET_SAMPLES_PER_LABEL and count >= TARGET_SAMPLES_PER_LABEL:
                break

            img_path = os.path.join(folder_path, img_file)
            if not img_path.lower().endswith(('.jpg','.png')):
                continue

            img = cv2.imread(img_path)
            if img is None:
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand in result.multi_hand_landmarks:
                    row = [label_map[folder]] + [coord for lm in hand.landmark for coord in (lm.x, lm.y, lm.z)]
                    with open(OUTPUT_CSV, "a", newline="") as f:
                        csv.writer(f).writerow(row)
                    count += 1

            processed_images += 1
            percent = (processed_images / total_images) * 100
            print(f"Progress: {processed_images}/{total_images} ({percent:.2f}%)", end="\r")

        print(f"\n✅ Processed {count} images for label: {folder}")

print("\n🎉 All images processed! CSV ready for training.")
