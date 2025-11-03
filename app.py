from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QProgressBar, QLabel, QMessageBox, QLineEdit
)
from PyQt5.QtCore import QProcess, Qt, QTimer
import sys, os


class GestureUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hand Gesture Recognition UI")
        self.resize(400, 300)

        # QProcess handles background scripts (training, collection, etc.)
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.on_finished)

        # Main layout setup
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.widgets = []

        self.show_main_screen()

    # ==================================================
    # MAIN SCREEN
    # ==================================================
    def show_main_screen(self):
        self.clear_layout(hide_only=True)

        title = QLabel("🖐️ Hand Gesture Recognition")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(title)

        self.btn_collect = QPushButton("📸 Collect Data")
        self.btn_train = QPushButton("🧠 Train Model")
        self.btn_recognize = QPushButton("🤚 Start Recognition")
        self.btn_reset = QPushButton("⚠️ Reset All")

        self.btn_collect.clicked.connect(self.show_collect_screen)
        self.btn_train.clicked.connect(self.show_train_screen)
        self.btn_recognize.clicked.connect(lambda: self.run_script("recognize_gesture.py", detached=True))
        self.btn_reset.clicked.connect(self.confirm_reset)

        for btn in [self.btn_collect, self.btn_train, self.btn_recognize, self.btn_reset]:
            self.layout.addWidget(btn)

        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.widgets = [
            title, self.btn_collect, self.btn_train,
            self.btn_recognize, self.btn_reset, self.status_label
        ]

    # ==================================================
    # COLLECT DATA
    # ==================================================
    def show_collect_screen(self):
        self.clear_layout()

        label = QLabel("Enter gesture label:")
        label.setAlignment(Qt.AlignCenter)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("e.g. open_palm, fist, peace")

        start_btn = QPushButton("Start Collecting")
        back_btn = QPushButton("⬅️ Back to Main Menu")

        start_btn.clicked.connect(self.start_collecting)
        back_btn.clicked.connect(self.show_main_screen)

        for w in [label, self.input_field, start_btn, back_btn]:
            self.layout.addWidget(w)

        self.widgets = [label, self.input_field, start_btn, back_btn]

    def start_collecting(self):
        gesture_name = self.input_field.text().strip()
        if not gesture_name:
            QMessageBox.warning(self, "Input Required", "Please enter a gesture name before starting.")
            return

        self.clear_layout(hide_only=True)
        status = QLabel(f"Collecting samples for '{gesture_name}'...")
        status.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(status)
        self.widgets = [status]

        # ✅ Run collect_data.py connected (not detached)
        self.run_script("collect_data.py", [gesture_name])

    # ==================================================
    # TRAIN MODEL
    # ==================================================
    def show_train_screen(self):
        self.clear_layout(hide_only=True)

        self.status_label = QLabel("Training model...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)

        self.widgets = [self.status_label, self.progress_bar]
        self.run_script("train_model.py")

    # ==================================================
    # RESET CONFIRMATION
    # ==================================================
    def confirm_reset(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Confirm Reset")
        msg.setText("⚠️ This will delete all gesture data and trained models.")
        msg.setInformativeText("Do you want to create a backup before deleting?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)

        choice = msg.exec_()
        if choice == QMessageBox.Yes:
            self.run_script("reset_all.py")
        elif choice == QMessageBox.No:
            self.run_script("reset_all.py", ["--no-backup"])
        else:
            if hasattr(self, "status_label"):
                self.status_label.setText("Reset canceled.")

    # ==================================================
    # UTILITIES
    # ==================================================
    def run_script(self, script, args=None, detached=False):
        """Run a script from gesture_scripts/ folder safely."""
        if args is None:
            args = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "gesture_scripts", script)

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Script not found:\n{script_path}")
            print(f"❌ Script not found: {script_path}")
            return

        print(f"▶ Running: {script_path} {' '.join(args)}")

        working_dir = os.path.dirname(script_path)

        if detached:
            # For OpenCV windows that run separately
            QProcess.startDetached(sys.executable, [script_path] + args, working_dir)
        else:
            # Connected process (UI receives stdout)
            self.process.setWorkingDirectory(working_dir)
            self.process.start(sys.executable, [script_path] + args)

        if hasattr(self, "status_label") and not detached:
            try:
                self.status_label.setText(f"Running {script}...")
            except RuntimeError:
                pass

    def read_output(self):
        """Handle stdout updates from background scripts."""
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8").strip()
        if not output:
            return

        print(output)  # For terminal debugging

        # Training progress tracking
        if hasattr(self, "progress_bar") and "PROGRESS:" in output:
            try:
                percent = int(output.split("PROGRESS:")[-1].split()[0])
                self.progress_bar.setValue(percent)
            except Exception:
                pass

        # ✅ Detect data collection completion
        if "COLLECTION_DONE" in output:
            QMessageBox.information(self, "Data Collection", "✅ Data collection complete!")
            QTimer.singleShot(500, self.show_main_screen)

    def on_finished(self):
        """Safely handle process completion (avoid deleted widget errors)."""
        try:
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.setText("✅ Process finished.")
        except RuntimeError:
            pass
        QTimer.singleShot(300, self.show_main_screen)

    def clear_layout(self, hide_only=False):
        """Safely hide or delete widgets."""
        for child in self.widgets:
            try:
                if hide_only:
                    child.hide()
                else:
                    child.setParent(None)
                    child.deleteLater()
            except RuntimeError:
                pass
        self.widgets = []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GestureUI()
    window.show()
    sys.exit(app.exec_())
