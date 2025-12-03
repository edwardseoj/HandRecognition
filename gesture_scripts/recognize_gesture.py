# recognize_gesture.py
import os
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import platform
import subprocess
import ctypes

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
# Load legacy H5 model safely
# ---------------------------------------------------------
import h5py

def load_legacy_h5_model(path):
    try:
        # Try direct load (works for TF 2.x)
        model = tf.keras.models.load_model(path, compile=False)
        print("✅ Loaded model directly with load_model")
        return model
    except Exception as e:
        print("⚠ Failed direct load, applying legacy patch...", e)
        # Legacy patch: remove DTypePolicy references in H5 attributes
        with h5py.File(path, 'r+') as f:
            if 'model_config' in f.attrs:
                raw = f.attrs['model_config']
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                raw = raw.replace('"DTypePolicy"', '"float32"')
                f.attrs['model_config'] = raw.encode('utf-8')
        # Retry load
        model = tf.keras.models.load_model(path, compile=False)
        print("✅ Loaded legacy H5 model with patch")
        return model

# Load model
model = load_legacy_h5_model(MODEL_PATH)

# ---------------------------------------------------------
# OS
# ---------------------------------------------------------
OS = platform.system().lower()
print("📌 Detected OS:", OS)

# ---------------------------------------------------------
# Spotify / media key
# ---------------------------------------------------------
def run_spotify_command(gesture):
    print("🎵 Gesture:", gesture)

    if OS == "linux":
        cmds = {
            "play": ["playerctl", "play"],
            "pause": ["playerctl", "pause"],
            "next": ["playerctl", "next"],
            "previous": ["playerctl", "previous"],
            "volume_up": ["playerctl", "volume", "0.1+"],
            "volume_down": ["playerctl", "volume", "0.1-"],
            "volume_25": ["playerctl", "volume", "0.25"],
            "volume_50": ["playerctl", "volume", "0.50"],
            "volume_75": ["playerctl", "volume", "0.75"],
            "volume_100": ["playerctl", "volume", "1.00"],
        }
        if gesture in cmds:
            subprocess.run(cmds[gesture])
        return

    elif OS == "darwin":
        cmds = {
            "play": 'tell application "Spotify" to play',
            "pause": 'tell application "Spotify" to pause',
            "next": 'tell application "Spotify" to next track',
            "previous": 'tell application "Spotify" to previous track',
            "volume_up": 'set sound volume to (sound volume + 10)',
            "volume_down": 'set sound volume to (sound volume - 10)',
            "volume_25": 'set sound volume to 25',
            "volume_50": 'set sound volume to 50',
            "volume_75": 'set sound volume to 75',
            "volume_100": 'set sound volume to 100',
        }
        if gesture in cmds:
            subprocess.run(["osascript", "-e", cmds[gesture]])
        return

    elif OS == "windows":
        VK = {
            "play": 0xB3,
            "pause": 0xB3,
            "next": 0xB0,
            "previous": 0xB1,
            "volume_up": 0xAF,
            "volume_down": 0xAE,
        }

        fixed_volume_cmds = {
            "volume_25": ["nircmd.exe", "setsysvolume", str(int(65535 * 0.25))],
            "volume_50": ["nircmd.exe", "setsysvolume", str(int(65535 * 0.50))],
            "volume_75": ["nircmd.exe", "setsysvolume", str(int(65535 * 0.75))],
            "volume_100": ["nircmd.exe", "setsysvolume", str(int(65535 * 1.00))],
        }

        if gesture in fixed_volume_cmds:
            subprocess.run(fixed_volume_cmds[gesture])
            print(f"✔ Windows volume set via nircmd: {gesture}")
            return

        key = VK.get(gesture)
        if key:
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)
            ctypes.windll.user32.keybd_event(key, 0, 2, 0)
            print(f"✔ Windows media key sent: {hex(key)}")


# ---------------------------------------------------------
# MediaPipe setup
# ---------------------------------------------------------
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

last = None
cooldown = 30
timer = 0

# ---------------------------------------------------------
# Main loop
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

                # Flatten landmarks
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
