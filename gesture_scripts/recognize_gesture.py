import os
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import platform
import subprocess
import ctypes
import json
import h5py

try:
    import keyboard
except ImportError:
    keyboard = None

# =======================
# OS DETECTION
# =======================
OS = platform.system().lower()
print("Detected OS:", OS)

if OS == "windows":
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER

# =======================
# PATHS
# =======================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.keras")
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model not found at: " + MODEL_PATH)
if not os.path.exists(LABEL_PATH):
    raise FileNotFoundError("Labels not found at: " + LABEL_PATH)

labels = np.load(LABEL_PATH, allow_pickle=True)

# Load keras model
model = tf.keras.models.load_model(MODEL_PATH)
print("Model loaded successfully")

# =======================
# LEGACY MODEL LOADER (SOLUTION 1)
# =======================
import json
import h5py
from tensorflow import keras

def load_legacy_h5_model(path):
    with h5py.File(path, "r") as f:
        model_config = f.attrs.get("model_config")
        if isinstance(model_config, bytes):
            model_config = model_config.decode("utf-8")

        config = json.loads(model_config)

        # ===== FIX InputLayer =====
        for layer in config["config"]["layers"]:
            cfg = layer["config"]

            if layer["class_name"] == "InputLayer":
                if "batch_shape" in cfg:
                    cfg["input_shape"] = cfg["batch_shape"][1:]
                    cfg.pop("batch_shape", None)

            # ===== FIX dtype policy (Keras 3) =====
            if "dtype" in cfg:
                dtype = cfg["dtype"]

                # Old serialized dtype object → string
                if isinstance(dtype, dict):
                    cfg["dtype"] = "float32"

        # ===== BUILD MODEL =====
        # model = keras.models.model_from_json(json.dumps(config))
        # model = tf.keras.models.load_model("models/gesture_model.keras")
        model = tf.keras.models.load_model(MODEL_PATH)
        model.load_weights(path)

    print("Legacy H5 model loaded with dtype + InputLayer patch")
    return model

# =======================
# WINDOWS VOLUME CONTROL
# =======================
def set_volume_windows(volume_percent):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMasterVolumeLevelScalar(volume_percent / 100.0, None)
        print(f"Volume set to {volume_percent}%")
    except Exception as e:
        print("Volume error:", e)

# =======================
# SPOTIFY COMMANDS
# =======================
def run_spotify_command(gesture):
    print("Gesture:", gesture)

    if OS == "darwin":
        cmds = {
            "play": 'tell application "Spotify" to play',
            "pause": 'tell application "Spotify" to pause',
            "next": 'tell application "Spotify" to next track',
            "previous": 'tell application "Spotify" to previous track',
            "volume_25": 'set sound volume to 25',
            "volume_50": 'set sound volume to 50',
            "volume_75": 'set sound volume to 75',
            "volume_100": 'set sound volume to 100',
        }
        if gesture in cmds:
            subprocess.run(["osascript", "-e", cmds[gesture]])

    elif OS == "windows":
        VK = {
            "play": 0xB3,
            "pause": 0xB3,
            "next": 0xB0,
            "previous": 0xB1,
            "volume_up": 0xAF,
            "volume_down": 0xAE,
        }

        fixed_volume = {
            "volume_25": 25,
            "volume_50": 50,
            "volume_75": 75,
            "volume_100": 100,
        }

        if gesture in fixed_volume:
            set_volume_windows(fixed_volume[gesture])
            return

        key = VK.get(gesture)
        if key:
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key, 0, 2, 0)

# =======================
# MEDIAPIPE SETUP
# =======================
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

last_gesture = None
cooldown = 30
timer = 0

# =======================
# MAIN LOOP
# =======================
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
) as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                row = []
                for lm in hand.landmark:
                    row.extend([lm.x, lm.y, lm.z])

                X = np.array(row).reshape(1, -1)

                pred = model.predict(X, verbose=0)
                gesture = labels[np.argmax(pred)]

                cv2.putText(frame, gesture, (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2)

                if timer <= 0 and gesture != last_gesture:
                    run_spotify_command(str(gesture))
                    last_gesture = gesture
                    timer = cooldown

        if timer > 0:
            timer -= 1

        cv2.imshow("Spotify Gesture Control", frame)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
