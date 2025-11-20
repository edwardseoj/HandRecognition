# recognize_gesture.py
import os
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import platform
import subprocess
import h5py
import json

try:
    import keyboard
except ImportError:
    keyboard = None

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model not found at: " + MODEL_PATH)
if not os.path.exists(LABEL_PATH):
    raise FileNotFoundError("Gesture labels not found at: " + LABEL_PATH)

labels = np.load(LABEL_PATH, allow_pickle=True)

# ---------------------------------------------------------
# FIX BROKEN OLD H5 MODELS
# ---------------------------------------------------------
def sanitize_layer_config(cfg):
    """Remove or rewrite legacy dtype fields that break TF 2.x"""

    # Remove dtype_policy
    if "dtype_policy" in cfg:
        cfg.pop("dtype_policy")

    # Remove old dtype stored as dict
    if "dtype" in cfg:
        if isinstance(cfg["dtype"], dict):
            cfg["dtype"] = "float32"
        elif "DTypePolicy" in str(cfg["dtype"]):
            cfg["dtype"] = "float32"

    # Handle batch_shape
    if "batch_shape" in cfg:
        cfg["batch_input_shape"] = cfg.pop("batch_shape")

    return cfg


def load_keras_model_safely(path):
    """Load legacy H5 model by rewriting its JSON config."""
    with h5py.File(path, "r") as f:
        raw = f.attrs.get("model_config")
        if raw is None:
            raise ValueError("❌ model_config missing in .h5 file")

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        config = json.loads(raw)

        # Patch layers
        for layer in config["config"]["layers"]:
            layer["config"] = sanitize_layer_config(layer["config"])

        # Build model
        model = tf.keras.models.model_from_json(json.dumps(config))

        # Load weights normally
        model.load_weights(path)

        return model


# LOAD THE MODEL SAFELY
model = load_keras_model_safely(MODEL_PATH)
print("✅ Model loaded successfully with dtype patches!")


# ---------------------------------------------------------
# OS
# ---------------------------------------------------------
OS = platform.system().lower()
print("📌 Detected OS:", OS)


# ---------------------------------------------------------
# Spotify
# ---------------------------------------------------------
def run_spotify_command(gesture):
    print("🎵 Gesture:", gesture)

    if OS == "linux":
        cmds = {
            "play": ["playerctl", "play"],
            "pause": ["playerctl", "pause"],
            "next": ["playerctl", "next"],
            "next2": ["playerctl", "next"],
            "previous": ["playerctl", "previous"],
            "previous2": ["playerctl", "previous"],
            "volume_up": ["playerctl", "volume", "0.1+"],
            "volume_down": ["playerctl", "volume", "0.1-"],
        }
        if gesture in cmds:
            subprocess.run(cmds[gesture])
        return

    if OS == "darwin":
        cmds = {
            "play": 'tell application "Spotify" to play',
            "pause": 'tell application "Spotify" to pause',
            "next": 'tell application "Spotify" to next track',
            "previous": 'tell application "Spotify" to previous track',
            "volume_up": 'set sound volume to (sound volume + 10)',
            "volume_down": 'set sound volume to (sound volume - 10)',
        }
        if gesture in cmds:
            subprocess.run(["osascript", "-e", cmds[gesture]])
        return

    if OS == "windows":
        cmds = {
            "play": "play/pause media",
            "pause": "play/pause media",
            "next": "next track media",
            "previous": "previous track media",
            "volume_up": "volume up",
            "volume_down": "volume down",
        }
        if gesture in cmds and keyboard:
            keyboard.send(cmds[gesture])
        return


# ---------------------------------------------------------
# MediaPipe
# ---------------------------------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

last = None
cooldown = 30
timer = 0


# ---------------------------------------------------------
# Main Loop
# ---------------------------------------------------------
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
) as hands:

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                # Flatten
                row = []
                for lm in hand.landmark:
                    row.extend([lm.x, lm.y, lm.z])

                X = np.array(row).reshape(1, -1)

                pred = model.predict(X, verbose=0)
                gesture = labels[np.argmax(pred)]

                cv2.putText(frame, str(gesture), (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                if timer <= 0 and gesture != last:
                    run_spotify_command(str(gesture))
                    last = gesture
                    timer = cooldown

        if timer > 0:
            timer -= 1

        cv2.imshow("Spotify Gesture Control", frame)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
