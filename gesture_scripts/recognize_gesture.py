# recognize_gesture.py
import os
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import platform
import subprocess
import ctypes
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
# Universal legacy H5 model loader
# ---------------------------------------------------------
def load_legacy_h5_model(path):
    try:
        # Try direct load first
        model = tf.keras.models.load_model(path, compile=False)
        print("✅ Loaded model directly")
        return model
    except Exception as e:
        print("⚠ Direct load failed, applying legacy patch...", e)
        
        with h5py.File(path, 'r+') as f:
            if 'model_config' in f.attrs:
                raw = f.attrs['model_config']
                if isinstance(raw, bytes):
                    raw = raw.decode('utf-8')
                config = json.loads(raw)

                # Fix top-level dtype
                if 'config' in config and 'dtype' in config['config']:
                    cfg_dtype = config['config']['dtype']
                    if isinstance(cfg_dtype, dict) or 'DTypePolicy' in str(cfg_dtype):
                        config['config']['dtype'] = 'float32'

                # Patch each layer
                for layer in config['config']['layers']:
                    cfg = layer.get('config', {})
                    # Remove dtype_policy
                    cfg.pop('dtype_policy', None)
                    # Fix dtype dicts
                    if 'dtype' in cfg and (isinstance(cfg['dtype'], dict) or 'DTypePolicy' in str(cfg['dtype'])):
                        cfg['dtype'] = 'float32'
                    # Rename batch_shape → batch_input_shape
                    if 'batch_shape' in cfg:
                        cfg['batch_input_shape'] = cfg.pop('batch_shape')
                    layer['config'] = cfg

                # Save patched config back to H5
                f.attrs['model_config'] = json.dumps(config).encode('utf-8')

        # Retry load
        model = tf.keras.models.load_model(path, compile=False)
        print("✅ Loaded legacy H5 model after patch")
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
            "next2": ["playerctl", "next"],
            "previous": ["playerctl", "previous"],
            "previous2": ["playerctl", "previous"],
            "volume_up": ["playerctl", "volume", "0.1+"],
            "volume_down": ["playerctl", "volume", "0.1-"],
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
        }
        if gesture in cmds:
            subprocess.run(["osascript", "-e", cmds[gesture]])
        return

    elif OS == "windows":
        VK = {
            "play":        0xB3,  # VK_MEDIA_PLAY_PAUSE
            "pause":       0xB3,
            "next":        0xB0,  # VK_MEDIA_NEXT_TRACK
            "previous":    0xB1,  # VK_MEDIA_PREV_TRACK
            "next2":        0xB0,  # VK_MEDIA_NEXT_TRACK
            "previous2":    0xB1,  # VK_MEDIA_PREV_TRACK
            "volume_up":   0xAF,  # VK_VOLUME_UP
            "volume_down": 0xAE,  # VK_VOLUME_DOWN
        }
        key = VK.get(gesture)
        if key:
            ctypes.windll.user32.keybd_event(key, 0, 0, 0)  # Press
            ctypes.windll.user32.keybd_event(key, 0, 2, 0)  # Release
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
