import tensorflow as tf
import numpy as np
import csv

# === 1. Load dataset manually from CSV ===
data = []
labels = []

with open('gesture_data/hand_gestures.csv', 'r') as f:
    reader = csv.reader(f)
    next(reader)  # skip header row
    for row in reader:
        # First column is label (string)
        label = row[0]
        # The rest are 63 landmark coordinates (x, y, z)
        features = [float(x) for x in row[1:]]
        data.append(features)
        labels.append(label)

# Convert to NumPy arrays
X = np.array(data, dtype=np.float32)
labels = np.array(labels)

# === 2. Encode text labels (without sklearn) ===
# Find all unique gesture names
unique_labels = np.unique(labels)
# Map each label to an integer (e.g., "fist" -> 0, "open_palm" -> 1, etc.)
label_to_index = {label: idx for idx, label in enumerate(unique_labels)}
# Convert string labels to integer IDs
y_int = np.array([label_to_index[label] for label in labels])

# === 3. Convert integer labels to one-hot vectors ===
num_classes = len(unique_labels)
y = tf.keras.utils.to_categorical(y_int, num_classes=num_classes)

# === 4. Define the TensorFlow model ===
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(63,)),          # 21 landmarks × (x, y, z)
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(num_classes, activation='softmax')
])

# === 5. Compile the model ===
model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# === 6. Train the model ===
history = model.fit(X, y, epochs=30, batch_size=16, validation_split=0.2)

# === 7. Save model and label list ===
model.save('gesture_model.h5')
np.save('gesture_labels.npy', unique_labels)

print("✅ Model training complete!")
print(f"Saved model as 'gesture_model.h5' and labels as 'gesture_labels.npy'")