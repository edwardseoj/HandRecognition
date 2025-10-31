import os
import csv
import shutil
import datetime
import numpy as np

# Paths (adjust if your project uses other names/locations)
DATA_DIR = 'gesture_data'
CSV_PATH = os.path.join(DATA_DIR, 'hand_gestures.csv')
MODEL_PATH = 'gesture_model.h5'
LABELS_PATH = 'gesture_labels.npy'
BACKUP_DIR_ROOT = 'backups'

def make_csv_header(path):
    """Create an empty CSV with the expected header for landmarks."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    header = ['label']
    for i in range(21):
        header += [f'x{i}', f'y{i}', f'z{i}']
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

def backup_files(backup_dir):
    """Copy existing artifacts into the backup directory."""
    os.makedirs(backup_dir, exist_ok=True)
    # Backup CSV directory if exists
    if os.path.exists(DATA_DIR):
        try:
            shutil.copytree(DATA_DIR, os.path.join(backup_dir, os.path.basename(DATA_DIR)))
        except Exception as e:
            # fallback: copy individual file if copytree fails
            if os.path.exists(CSV_PATH):
                shutil.copy2(CSV_PATH, backup_dir)
    # Backup model file
    if os.path.exists(MODEL_PATH):
        shutil.copy2(MODEL_PATH, backup_dir)
    # Backup labels file
    if os.path.exists(LABELS_PATH):
        shutil.copy2(LABELS_PATH, backup_dir)

def reset_all(make_backup=True):
    """Reset dataset and model artifacts."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    if make_backup:
        backup_dir = os.path.join(BACKUP_DIR_ROOT, f'backup_{timestamp}')
        print(f"Creating backup at: {backup_dir}")
        backup_files(backup_dir)
        print("Backup complete.")

    # Remove gesture data directory entirely (if exists)
    if os.path.exists(DATA_DIR):
        print(f"Deleting data directory: {DATA_DIR}")
        shutil.rmtree(DATA_DIR)
    else:
        print(f"No data directory found at: {DATA_DIR} (nothing to delete)")

    # Recreate clean data directory and CSV header
    print("Recreating data directory and CSV header...")
    os.makedirs(DATA_DIR, exist_ok=True)
    make_csv_header(CSV_PATH)
    print(f"Created empty CSV: {CSV_PATH}")

    # Delete model file if it exists
    if os.path.exists(MODEL_PATH):
        print(f"Deleting model file: {MODEL_PATH}")
        os.remove(MODEL_PATH)
    else:
        print(f"No model file found at: {MODEL_PATH}")

    # Delete labels file if it exists
    if os.path.exists(LABELS_PATH):
        print(f"Deleting labels file: {LABELS_PATH}")
        os.remove(LABELS_PATH)
    else:
        print(f"No labels file found at: {LABELS_PATH}")

    # Recreate an empty labels.npy so other scripts expecting it won't throw file-not-found.
    print("Creating empty labels file (gesture_labels.npy) ...")
    np.save(LABELS_PATH, np.array([]))
    print("Reset complete.")

if __name__ == "__main__":
    print("⚠️  This script will delete your gesture dataset and model files.")
    choice = input("Do you want to create a backup before deleting? (Y/n): ").strip().lower()
    make_backup = True if choice in ['', 'y', 'yes'] else False

    confirm = input("Type 'RESET' to proceed (or anything else to cancel): ").strip()
    if confirm == 'RESET':
        reset_all(make_backup=make_backup)
    else:
        print("Aborted. No changes made.")