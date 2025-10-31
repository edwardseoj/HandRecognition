import cv2
import mediapipe as mp
import csv
import os
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

DATA_DIR = 'gesture_data'
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, 'hand_gestures.csv')

# Create CSV header if not exist
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['label']
        for i in range(21):
            header += [f'x{i}', f'y{i}', f'z{i}']
        writer.writerow(header)

cap = cv2.VideoCapture(0)
gesture_label = input("Enter gesture label (e.g., open_palm): ")

# How many samples to collect
target_samples = 200
count = 0

with mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                    min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:

    print("Starting collection in 3 seconds...")
    time.sleep(3)
    print(f"Collecting {target_samples} samples for '{gesture_label}'...")

    while cap.isOpened() and count < target_samples:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Extract landmark coordinates
                row = [gesture_label]
                for lm in hand_landmarks.landmark:
                    row += [lm.x, lm.y, lm.z]

                # Save one row per frame
                with open(CSV_PATH, 'a', newline='') as f:
                    csv.writer(f).writerow(row)
                count += 1

                # Draw hand + show sample count
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                cv2.putText(image, f'Samples: {count}/{target_samples}', (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

        cv2.imshow('Collecting Data', image)

        # Optional: stop early with 'q'
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    print(f"✅ Finished collecting {count} samples for '{gesture_label}'")

cap.release()
cv2.destroyAllWindows()
