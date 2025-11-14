import os
import cv2
import mediapipe as mp
import numpy as np
import tensorflow as tf
import subprocess
import platform

# Windows media key library (safe to import but used only on Windows)
try:
    import keyboard
except:
    keyboard = None

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model not found. Train the model first.")

model = tf.keras.models.load_model(MODEL_PATH)
labels = np.load(LABEL_PATH, allow_pickle=True)

# --------------------------------------------------------------------
# OS Detection
# --------------------------------------------------------------------
OS = platform.system().lower()
print(f"📌 Running on: {OS}")

# --------------------------------------------------------------------
# Spotify Controller
# --------------------------------------------------------------------
def run_spotify_command(gesture):
    """Run a mapped Spotify command based on the OS."""
    print(f"🎵 Gesture recognized: {gesture}")

    # -------------------- Linux (playerctl) --------------------
    if OS == "linux":
        linux_cmds = {
            "play":        ["playerctl", "play"],
            "pause":       ["playerctl", "pause"],
            "next":        ["playerctl", "next"],
            "previous":    ["playerctl", "previous"],
            "volume_up":   ["playerctl", "volume", "0.1+"],
            "volume_down": ["playerctl", "volume", "0.1-"],
        }
        cmd = linux_cmds.get(gesture)
        if cmd:
            subprocess.run(cmd)
            print(f"✔ Linux command executed: {cmd}")
        return

    # -------------------- macOS (AppleScript) --------------------
    if OS == "darwin":
        mac_cmds = {
            "play":        'tell application "Spotify" to play',
            "pause":       'tell application "Spotify" to pause',
            "next":        'tell application "Spotify" to next track',
            "previous":    'tell application "Spotify" to previous track',
            "volume_up":   'set sound volume to (sound volume + 10)',
            "volume_down": 'set sound volume to (sound volume - 10)',
        }
        script = mac_cmds.get(gesture)
        if script:
            subprocess.run(["osascript", "-e", script])
            print(f"✔ macOS AppleScript executed.")
        return

    # -------------------- Windows (media keys) --------------------
    if OS == "windows":
        win_cmds = {
            "play":        "play/pause media",
            "pause":       "play/pause media",
            "next":        "next track media",
            "previous":    "previous track media",
            "volume_up":   "volume up",
            "volume_down": "volume down",
        }
        key = win_cmds.get(gesture)
        if key and keyboard:
            keyboard.send(key)
            print(f"✔ Windows media key sent: {key}")
        return

    print("⚠ Unsupported OS or command.")

# --------------------------------------------------------------------
# MediaPipe Initialization
# --------------------------------------------------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

last_action = None
cooldown_frames = 30
frame_counter = 0

# --------------------------------------------------------------------
# Main Loop
# --------------------------------------------------------------------
with mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            continue

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                # Flatten x,y,z coordinates
                row = [coord for lm in hand.landmark for coord in (lm.x, lm.y, lm.z)]
                X = np.array(row).reshape(1, -1)

                pred = model.predict(X, verbose=0)
                gesture = labels[np.argmax(pred)]

                cv2.putText(frame, str(gesture), (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0, 255, 0), 2)

                # Cooldown system
                if frame_counter <= 0 and gesture != last_action:
                    run_spotify_command(gesture)
                    last_action = gesture
                    frame_counter = cooldown_frames

        if frame_counter > 0:
            frame_counter -= 1

        cv2.imshow("Spotify Gesture Control", frame)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
