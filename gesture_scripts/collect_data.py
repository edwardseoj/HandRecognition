import sys, os, time, csv, cv2, mediapipe as mp

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "gesture_data")
CSV_PATH = os.path.join(DATA_DIR, "hand_gestures.csv")
LABELS_PATH = os.path.join(DATA_DIR, "gesture_labels.csv")

os.makedirs(DATA_DIR, exist_ok=True)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Create CSV header if missing
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="") as f:
        header = ["label"] + [f"{c}{i}" for i in range(21) for c in ("x", "y", "z")]
        csv.writer(f).writerow(header)

# Get gesture name from argument or input
gesture_label = sys.argv[1] if len(sys.argv) > 1 else input("Enter gesture label: ")
target_samples, count = 200, 0
cap = cv2.VideoCapture(0)

# ✅ Update gesture_labels.csv file
if not os.path.exists(LABELS_PATH):
    with open(LABELS_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["gesture_name"])

# Read existing labels
with open(LABELS_PATH, "r") as f:
    existing_labels = [row[0] for row in csv.reader(f)][1:]  # skip header

# Add new gesture if not already listed
if gesture_label not in existing_labels:
    with open(LABELS_PATH, "a", newline="") as f:
        csv.writer(f).writerow([gesture_label])
    print(f"🆕 Added new gesture label: '{gesture_label}' to gesture_labels.csv")

# ✅ Start collecting samples
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:
    print("Starting collection in 3 seconds...")
    time.sleep(3)
    print(f"Collecting {target_samples} samples for '{gesture_label}'")

    while cap.isOpened() and count < target_samples:
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                row = [gesture_label] + [coord for lm in hand.landmark for coord in (lm.x, lm.y, lm.z)]
                with open(CSV_PATH, "a", newline="") as f:
                    csv.writer(f).writerow(row)
                count += 1

                mp_drawing.draw_landmarks(image, hand, mp_hands.HAND_CONNECTIONS)
                cv2.putText(image, f"{count}/{target_samples}", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Collecting Data", image)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

print(f"✅ Collected {count} samples for '{gesture_label}'")
cap.release()
cv2.destroyAllWindows()

# ✅ Notify UI when done
print("COLLECTION_DONE", flush=True)
