import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QProgressBar, QLabel, QMessageBox, QLineEdit, QHBoxLayout,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import QProcess, Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QUrl
from PyQt5.QtGui import QMovie, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtGui import QIcon

# ==================================================
# INTRO SCREEN
# ==================================================
class IntroScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.logo = QLabel("""
        <span style='color:white;'>Hello, My name is</span>
        <span style='color:#00e5ff;'>C</span>
        <span style='color:#00d4ff;'>A</span>
        <span style='color:#00c3ff;'>L</span>
        <span style='color:#00b2ff;'>I</span>
        <span style='color:#009eff;'>R</span>
        <span style='color:#008aff;'>A</span>
    """, self)

        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setTextFormat(Qt.RichText)

        font = QFont("Arial", 80)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 4)
        font.setBold(True)
        self.logo.setFont(font)

        self.logo.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(0,0,0,90);
                padding: 25px 50px;
                border-radius: 35px;
                border: 4px solid rgba(0,240,255,0.7);
            }
        """)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        glow.setColor(Qt.cyan)
        self.logo.setGraphicsEffect(glow)
        self.logo.hide()

        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(2000)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.InOutQuad)

        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(1500)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.InOutQuad)

        self.scale_anim = QPropertyAnimation(self.logo, b"geometry")
        self.scale_anim.setDuration(1200)
        self.scale_anim.setEasingCurve(QEasingCurve.OutQuad)

    def start(self, callback):
        self.callback = callback
        self.showFullScreen()
        self.setCursor(Qt.BlankCursor)
        screen_rect = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_rect)
        QTimer.singleShot(500, self.show_calira_logo)

    def show_calira_logo(self):
        self.logo.show()
        screen_rect = QApplication.primaryScreen().geometry()
        logo_rect = self.logo.geometry()
        center_x = (screen_rect.width() - logo_rect.width()) // 2
        center_y = (screen_rect.height() - logo_rect.height()) // 2

        start_rect = QRect(center_x + logo_rect.width() // 2, center_y + logo_rect.height() // 2, 0, 0)
        end_rect = QRect(center_x, center_y, logo_rect.width(), logo_rect.height())

        self.logo.setGeometry(start_rect)
        self.scale_anim.setStartValue(start_rect)
        self.scale_anim.setEndValue(end_rect)
        self.scale_anim.start()

        self.fade_in.finished.connect(lambda: QTimer.singleShot(1500, lambda: self.fade_out_and_launch()))
        self.fade_in.start()

    def fade_out_and_launch(self):
        self.fade_out.finished.connect(lambda: (self.close(), self.callback()))
        self.fade_out.start()


# ==================================================
# MAIN UI
# ==================================================
class GestureUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/calira_icon.png"))
        self.setWindowTitle("CALIRA - Hand Gesture Recognition")
        self.resize(400, 300)
        self.setStyleSheet("background: transparent;")

        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()

        self.movie = QMovie("assets/background.gif")
        self.movie.setScaledSize(self.size())
        self.background_label.setMovie(self.movie)
        self.movie.start()

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.on_finished)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.widgets = []

        self.show_main_screen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.movie.setScaledSize(self.size())
        if hasattr(self, "title_letters"):
            self.animate_title()
    
    
    def show_main_screen(self):
        self.clear_layout(hide_only=True)
        self.showFullScreen()
        
        self.logo_label = QLabel("""
        <span style='color:#00e5ff;'>C</span>
        <span style='color:#00d4ff;'>A</span>
        <span style='color:#00c3ff;'>L</span>
        <span style='color:#00b2ff;'>I</span>
        <span style='color:#009eff;'>R</span>
        <span style='color:#008aff;'>A</span>
    """)
    
        self.logo_label.setTextFormat(Qt.RichText)

        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 80, QFont.Bold))

        self.logo_label.setStyleSheet("""
            QLabel {
                font-size: 80px;
                font-weight: bold;
                margin-bottom: 80px;
            }
        """)

        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setColor(Qt.cyan)
        glow.setOffset(0)
        self.logo_label.setGraphicsEffect(glow)

        self.layout.addWidget(self.logo_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        button_layout.setContentsMargins(40, 20, 40, 20)

        self.btn_collect = QPushButton("Collect Data")
        self.btn_train = QPushButton("Train Model")
        self.btn_recognize = QPushButton("Start Recognition")
        self.btn_reset = QPushButton("Reset All")

        for btn in [self.btn_collect, self.btn_train, self.btn_recognize, self.btn_reset]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setMinimumHeight(100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #324AB2;
                    color: #00FFFF;
                    font-size: 16px;
                    font-weight: bold;
                    font-family: 'Arial', sans-serif;
                    border: 2px solid rgb(0, 121, 88);
                    border-radius: 12px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: blue;
                    color: white;
                    border-color: white;
                }
            """)
            button_layout.addWidget(btn)

        self.layout.addLayout(button_layout)

        # ✅ Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: yellow; font-size: 14px; margin-top: 20px;")
        self.layout.addWidget(self.status_label)

        # ✅ Connect buttons
        self.btn_collect.clicked.connect(self.show_collect_screen)
        self.btn_train.clicked.connect(self.show_train_screen)
        self.btn_recognize.clicked.connect(lambda: self.run_script("recognize_gesture.py", detached=True))
        self.btn_reset.clicked.connect(self.confirm_reset)

        self.widgets = [
            self.logo_label, self.btn_collect, self.btn_train,
            self.btn_recognize, self.btn_reset, self.status_label
        ]


    def animate_title(self):
        for i in range(len(self.title_letters)):
            anim = getattr(self, f"anim_{i}", None)
            if anim:
                anim.stop()

    def start_animation():
        for i, letter in enumerate(self.title_letters):
            rect = letter.geometry()
            if rect.isValid():
                bounce_height = max(10, int(rect.height() * 0.2))
                anim = QPropertyAnimation(letter, b"geometry", self)
                anim.setDuration(3800)
                anim.setStartValue(rect)
                anim.setEndValue(QRect(rect.x(), rect.y() - bounce_height, rect.width(), rect.height()))
                anim.setEasingCurve(QEasingCurve.OutBounce)
                anim.setLoopCount(-1)
                QTimer.singleShot(i * 400, anim.start)
                setattr(self, f"anim_{i}", anim)

            QTimer.singleShot(300, start_animation)

    def show_collect_screen(self):
        self.clear_layout()

        label = QLabel("Enter gesture label:")
        label.setAlignment(Qt.AlignCenter)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("e.g. open_palm, fist, peace")

        start_btn = QPushButton("Start Collecting")
        back_btn = QPushButton("⬅Back to Main Menu")

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

        
        self.run_script("collect_data.py", [gesture_name])

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

    def run_script(self, script, args=None, detached=False):
        if args is None:
            args = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "gesture_scripts", script)

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Script not found:\n{script_path}")
            print(f"Script not found: {script_path}")
            return

        print(f"▶ Running: {script_path} {' '.join(args)}")

        working_dir = os.path.dirname(script_path)

        if detached:
            QProcess.startDetached(sys.executable, [script_path] + args, working_dir)
        else:
            self.process.setWorkingDirectory(working_dir)
            self.process.start(sys.executable, [script_path] + args)

        if hasattr(self, "status_label") and not detached:
            try:
                self.status_label.setText(f"Running {script}...")
            except RuntimeError:
                pass

    def read_output(self):
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8").strip()
        if not output:
            return

        print(output)

        if hasattr(self, "progress_bar") and "PROGRESS:" in output:
            try:
                percent = int(output.split("PROGRESS:")[1].split()[0])
                self.progress_bar.setValue(min(max(percent, 0), 100))
            except Exception:
                pass

        if "COLLECTION_DONE" in output:
            QMessageBox.information(self, "Data Collection", "✅ Data collection complete!")
            QTimer.singleShot(500, self.show_main_screen)

    def on_finished(self):
        try:
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.setText("Process finished.")
        except RuntimeError:
            pass
        QTimer.singleShot(300, self.show_main_screen)

    def clear_layout(self, hide_only=False):
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

# ==================================================
# MAIN ENTRY POINT
# ==================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/calira_icon.png"))

    def launch_main():
        window = GestureUI()
        window.show()

    intro = IntroScreen()
    intro.start(launch_main)

    sys.exit(app.exec_())
