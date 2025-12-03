import numpy as np
import os

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")

if not os.path.exists(LABEL_PATH):
    raise FileNotFoundError("gesture_labels.npy not found at: " + LABEL_PATH)

# ---------------------------------------------------------
# Load labels
# ---------------------------------------------------------
labels = np.load(LABEL_PATH, allow_pickle=True)
print("Current labels:", list(labels))

# ---------------------------------------------------------
# User renaming loop
# ---------------------------------------------------------
print("\nEnter new names. Leave blank to keep the label unchanged.\n")

new_labels = []

for old in labels:
    new_name = input(f"Rename '{old}' → ").strip()

    # Empty input = keep old
    if new_name == "":
        new_labels.append(old)
    else:
        new_labels.append(new_name)

new_labels = np.array(new_labels, dtype=object)

# ---------------------------------------------------------
# Save new label list
# ---------------------------------------------------------
np.save(LABEL_PATH, new_labels)

print("\n✅ gesture_labels.npy updated!")
print("Final labels:", list(new_labels))
print("\nYou can now run recognize_gesture.py and see the new names.")
