# train_model.py
import tensorflow as tf
import numpy as np
import csv, os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "gesture_data", "hand_gestures.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")
os.makedirs(os.path.join(BASE_DIR, "models"), exist_ok=True)

data, labels = [], []
with open(CSV_PATH, "r") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        labels.append(row[0])
        data.append([float(x) for x in row[1:]])

X = np.array(data, dtype=np.float32)
labels = np.array(labels)
unique_labels = np.unique(labels)
label_to_index = {label: i for i, label in enumerate(unique_labels)}
y_int = np.array([label_to_index[l] for l in labels])
y = tf.keras.utils.to_categorical(y_int, len(unique_labels))

model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(63,)),
    tf.keras.layers.Dense(128, activation='relu'),
    tf.keras.layers.Dropout(0.3),
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.Dense(len(unique_labels), activation='softmax')
])
model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

EPOCHS, BATCH = 30, 16

class ProgressPrinter(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs=None):
        print(f"PROGRESS:{int(((epoch + 1) / EPOCHS) * 100)} %", flush=True)

model.fit(X, y, epochs=EPOCHS, batch_size=BATCH, validation_split=0.2, callbacks=[ProgressPrinter()])
model.save(MODEL_PATH)
np.save(LABEL_PATH, unique_labels)
print("TRAINING_DONE", flush=True)
