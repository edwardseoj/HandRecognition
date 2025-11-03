import os, csv, shutil, datetime, numpy as np, sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "gesture_data")
MODEL_PATH = os.path.join(BASE_DIR, "models", "gesture_model.h5")
LABELS_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")
BACKUP_ROOT = os.path.join(BASE_DIR, "backups")
CSV_PATH = os.path.join(DATA_DIR, "hand_gestures.csv")

def make_csv_header(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ["label"] + [f"{c}{i}" for i in range(21) for c in ("x", "y", "z")]
    with open(path, "w", newline="") as f:
        csv.writer(f).writerow(header)

def backup_files(backup_dir):
    os.makedirs(backup_dir, exist_ok=True)
    for path in [DATA_DIR, MODEL_PATH, LABELS_PATH]:
        if os.path.exists(path):
            target = os.path.join(backup_dir, os.path.basename(path))
            if os.path.isdir(path):
                shutil.copytree(path, target)
            else:
                shutil.copy2(path, target)

def reset_all(make_backup=True):
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if make_backup:
        backup_dir = os.path.join(BACKUP_ROOT, f"backup_{timestamp}")
        print(f"Backing up to {backup_dir}")
        backup_files(backup_dir)

    if os.path.exists(DATA_DIR): shutil.rmtree(DATA_DIR)
    make_csv_header(CSV_PATH)

    for path in [MODEL_PATH, LABELS_PATH]:
        if os.path.exists(path): os.remove(path)
    np.save(LABELS_PATH, np.array([]))
    print("✅ Reset complete.")

if __name__ == "__main__":
    no_backup = "--no-backup" in sys.argv
    reset_all(make_backup=not no_backup)
