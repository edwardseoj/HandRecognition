# process_kaggle_dataset.py

import os
import csv
import cv2
import mediapipe as mp
from tqdm import tqdm  # progress bar

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
# STEP 3: Process images
# -------------------------------
labels = [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
total_labels = len(labels)

with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands, tqdm(total=total_labels, desc="Overall Progress", unit="label") as overall_bar:
    for label in labels:
        label_path = os.path.join(DATA_DIR, label)
        img_files = os.listdir(label_path)
        count = 0

        # Progress bar for images in this label
        for img_file in tqdm(img_files, desc=f"Processing '{label}'", unit="img", leave=False):
            if TARGET_SAMPLES_PER_LABEL and count >= TARGET_SAMPLES_PER_LABEL:
                break

            img_path = os.path.join(label_path, img_file)
            img = cv2.imread(img_path)
            if img is None:
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand in result.multi_hand_landmarks:
                    row = [label] + [coord for lm in hand.landmark for coord in (lm.x, lm.y, lm.z)]
                    with open(OUTPUT_CSV, "a", newline="") as f:
                        csv.writer(f).writerow(row)
                    count += 1

        tqdm.write(f"✅ Finished {count} images for label: {label}")
        overall_bar.update(1)

print("\n🎉 All images processed! CSV ready for training.")
