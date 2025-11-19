import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout,
    QProgressBar, QLabel, QMessageBox, QLineEdit, QHBoxLayout,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import QProcess, Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QMovie, QFont, QIcon


# ==================================================
# CUSTOM APP BAR (ONLY FOR MAIN UI)
# ==================================================
class AppBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.setFixedHeight(45)
        self.setStyleSheet("""
            background-color: rgba(0, 0, 0, 140);
            border-bottom: 2px solid cyan;
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 10, 0)

        title = QLabel("CALIRA - Gesture Recognition")
        title.setStyleSheet("color: cyan; font-size: 18px;")
        layout.addWidget(title)
        layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setFixedSize(40, 28)
        btn_min.setStyleSheet(self.btn_style())
        btn_min.clicked.connect(self.minimize)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(40, 28)
        btn_close.setStyleSheet(self.btn_style())
        btn_close.clicked.connect(self.close_app)

        layout.addWidget(btn_min)
        layout.addWidget(btn_close)

        self.setLayout(layout)
        self.drag_pos = None

    def btn_style(self):
        return """
            QPushButton {
                color: white;
                font-size: 18px;
                border: none;
                background: transparent;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 160);
            }
        """

    def minimize(self):
        self.parent.showMinimized()

    def close_app(self):
        self.parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.drag_pos:
            diff = event.globalPos() - self.drag_pos
            self.parent.move(self.parent.x() + diff.x(),
                             self.parent.y() + diff.y())
            self.drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None


# ==================================================
# INTRO SCREEN (UNCHANGED)
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

        start_rect = QRect(center_x + logo_rect.width() // 2,
                           center_y + logo_rect.height() // 2, 0, 0)
        end_rect = QRect(center_x, center_y,
                         logo_rect.width(), logo_rect.height())

        self.logo.setGeometry(start_rect)
        self.scale_anim.setStartValue(start_rect)
        self.scale_anim.setEndValue(end_rect)
        self.scale_anim.start()

        self.fade_in.finished.connect(
            lambda: QTimer.singleShot(1500, self.fade_out_and_launch)
        )
        self.fade_in.start()

    def fade_out_and_launch(self):
        self.fade_out.finished.connect(lambda: (self.close(), self.callback()))
        self.fade_out.start()


# ==================================================
# MAIN UI + APP BAR
# ==================================================
class GestureUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/calira_icon.png"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(400, 300)
        self.setStyleSheet("background: transparent;")

        # Background GIF
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()

        self.movie = QMovie("assets/background.gif")
        self.movie.setScaledSize(self.size())
        self.background_label.setMovie(self.movie)
        self.movie.start()

        # QProcess
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.finished.connect(self.on_finished)

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # AppBar
        self.appbar = AppBar(self)
        self.layout.addWidget(self.appbar)

        self.widgets = []
        self.show_main_screen()

    # -------------------
    # Events
    # -------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.movie.setScaledSize(self.size())

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowNoState:
                QTimer.singleShot(50, self.showFullScreen)

    # -------------------
    # Main screen
    # -------------------
    def show_main_screen(self):
        self.clear_layout(hide_only=False, skip=[self.appbar])
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
                    border-radius: 12px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #324AB2;
                    color: white;
                }
            """)
            button_layout.addWidget(btn)

        self.layout.addLayout(button_layout)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: yellow; font-size: 14px; margin-top: 20px;")
        self.layout.addWidget(self.status_label)

        # Connect buttons
        self.btn_collect.clicked.connect(self.show_collect_screen)
        self.btn_train.clicked.connect(self.show_train_screen)
        self.btn_recognize.clicked.connect(lambda: self.run_script("recognize_gesture.py", detached=True))
        self.btn_reset.clicked.connect(self.confirm_reset)

        self.widgets = [self.logo_label, self.btn_collect, self.btn_train,
                        self.btn_recognize, self.btn_reset, self.status_label]

    # -------------------
    # Other screens
    # -------------------
    def show_collect_screen(self):
        self.clear_layout(skip=[self.appbar])

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

    def show_train_screen(self):
        self.clear_layout(skip=[self.appbar])

        self.status_label = QLabel("Training model...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)

        self.widgets = [self.status_label, self.progress_bar]
        self.run_script("train_model.py")

    # -------------------
    # Reset
    # -------------------
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

    # -------------------
    # Process handling
    # -------------------
    def start_collecting(self):
        gesture_name = self.input_field.text().strip()
        if not gesture_name:
            QMessageBox.warning(self, "Input Required", "Please enter a gesture name before starting.")
            return

        self.clear_layout(hide_only=True, skip=[self.appbar])
        status = QLabel(f"Collecting samples for '{gesture_name}'...")
        status.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(status)
        self.widgets = [status]

        self.run_script("collect_data.py", [gesture_name])

    def run_script(self, script, args=None, detached=False):
        if args is None:
            args = []

        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "gesture_scripts", script)

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Script not found:\n{script_path}")
            return

        working_dir = os.path.dirname(script_path)

        if detached:
            QProcess.startDetached(sys.executable, [script_path] + args, working_dir)
        else:
            self.process.setWorkingDirectory(working_dir)
            self.process.start(sys.executable, [script_path] + args)

        if hasattr(self, "status_label") and not detached:
            self.status_label.setText(f"Running {script}...")

    def read_output(self):
        output = bytes(self.process.readAllStandardOutput()).decode("utf-8").strip()
        if not output:
            return

        print(output)

        if hasattr(self, "progress_bar") and "PROGRESS:" in output:
            try:
                p = int(output.split("PROGRESS:")[1].split()[0])
                self.progress_bar.setValue(max(0, min(100, p)))
            except:
                pass

        if "COLLECTION_DONE" in output:
            QMessageBox.information(self, "Data Collection", "Data collection complete!")
            QTimer.singleShot(500, self.show_main_screen)

    def on_finished(self):
        if hasattr(self, "status_label"):
            self.status_label.setText("Process finished.")
        QTimer.singleShot(400, self.show_main_screen)

    # -------------------
    # Layout cleaner
    # -------------------
    def clear_layout(self, hide_only=False, skip=[]):
        for child in self.widgets:
            if child in skip:
                continue
            try:
                if hide_only:
                    child.hide()
                else:
                    child.setParent(None)
                    child.deleteLater()
            except RuntimeError:
                pass

        self.widgets = skip.copy()



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
