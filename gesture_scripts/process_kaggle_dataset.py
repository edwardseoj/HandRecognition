# process_kaggle_dataset.py

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
# STEP 3: Process images
# -------------------------------
with mp_hands.Hands(static_image_mode=True, max_num_hands=1) as hands:
    for label in os.listdir(DATA_DIR):
        label_path = os.path.join(DATA_DIR, label)
        if not os.path.isdir(label_path):
            continue

        print(f"📂 Processing label: {label}")

        count = 0
        for img_file in os.listdir(label_path):
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

        print(f"✅ Processed {count} images for label: {label}")

print("🎉 All images processed! CSV ready for training.")
