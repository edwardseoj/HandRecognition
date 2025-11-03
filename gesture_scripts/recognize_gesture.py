import os, cv2, mediapipe as mp, numpy as np, tensorflow as tf, subprocess

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model not found. Train the model first.")

model = tf.keras.models.load_model(MODEL_PATH)
labels = np.load(LABEL_PATH, allow_pickle=True)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

# 🎵 Gesture → Spotify command mapping
GESTURE_COMMANDS = {
    "play": ["playerctl", "play-pause"],
    "pause": ["playerctl", "play-pause"],
    "next": ["playerctl", "next"],
    "previous": ["playerctl", "previous"],
    "volume_up": ["playerctl", "volume", "0.1+"],
    "volume_down": ["playerctl", "volume", "0.1-"],
}

last_action = None
cooldown_frames = 30  # frames before allowing new command
frame_counter = 0

def run_spotify_command(gesture):
    """Run a mapped Spotify command using playerctl."""
    if gesture in GESTURE_COMMANDS:
        cmd = GESTURE_COMMANDS[gesture]
        subprocess.run(cmd)
        print(f"🎶 Executed command for gesture: {gesture}")
    else:
        print(f"⚠️ No Spotify command mapped for gesture: {gesture}")

# ✅ Main recognition loop
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
                row = [coord for lm in hand.landmark for coord in (lm.x, lm.y, lm.z)]
                X = np.array(row).reshape(1, -1)
                pred = model.predict(X, verbose=0)
                gesture = labels[np.argmax(pred)]
                cv2.putText(frame, gesture, (10, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # 🧠 Cooldown-based gesture trigger
                if frame_counter <= 0 and gesture != last_action:
                    run_spotify_command(gesture)
                    last_action = gesture
                    frame_counter = cooldown_frames

        # Decrease cooldown timer
        if frame_counter > 0:
            frame_counter -= 1

        cv2.imshow("Spotify Gesture Control", frame)
        if cv2.waitKey(5) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
