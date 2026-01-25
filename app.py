import sys, os, traceback, re
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QDialog,
    QScrollArea, QProgressBar, QTextEdit, QGraphicsDropShadowEffect,
    QHBoxLayout, QLineEdit
)
from PyQt5.QtCore import QProcess, Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt5.QtGui import QMovie, QFont, QIcon
import numpy as np

class AppBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(48)
        self.setStyleSheet("""
            background-color: rgba(20, 20, 20, 180);
            border-bottom: 2px solid #00e5ff;
        """)
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 0, 12, 0)
        title = QLabel("CALIRA AI - Gesture Recognition")
        title.setStyleSheet("color: #00e5ff; font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setObjectName("minimize")
        btn_max = QPushButton("❐")
        btn_max.setObjectName("maximize")
        btn_close = QPushButton("✕")
        btn_close.setObjectName("exit")

        for btn in (btn_min, btn_max, btn_close):
            btn.setFixedSize(40, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(self.btn_style())
            layout.addWidget(btn)

        btn_min.clicked.connect(self.minimize)
        btn_max.clicked.connect(self.maximize_restore)
        btn_close.clicked.connect(self.close_app)

        self.setLayout(layout)
        self.drag_pos = None
        self.setStyleSheet(self.btn_style())

    def btn_style(self):
        return """
            QPushButton {
                color: white;
                font-size: 17px;
                border: 2px solid black;
                background-color: gray;
                border-radius: 6px;
            }
            QPushButton#minimize:hover { background-color: yellow; color: black }
            QPushButton#minimize:pressed { background-color: golden-rod; color: black; }
            QPushButton#maximize:hover { background-color: green; }
            QPushButton#maximize:pressed { background-color: dark-green; }
            QPushButton#exit:hover { background-color: red; }
            QPushButton#exit:pressed { background-color: dark-red; }
        """

    def minimize(self):
        self.parent.showMinimized()

    def maximize_restore(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
        else:
            self.parent.showMaximized()

    def close_app(self):
        self.parent.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.drag_pos:
            diff = event.globalPos() - self.drag_pos
            self.parent.move(self.parent.x() + diff.x(), self.parent.y() + diff.y())
            self.drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

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
        self.fade_in.finished.connect(lambda: QTimer.singleShot(1500, self.fade_out_and_launch))
        self.fade_in.start()

    def fade_out_and_launch(self):
        self.fade_out.finished.connect(lambda: (self.close(), self.callback()))
        self.fade_out.start()

class GestureUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/calira_icon.png"))
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(400, 300)
        self.setStyleSheet("background: transparent;")
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.lower()
        self.movie = QMovie("assets/background.gif")
        self.movie.setScaledSize(self.size())
        self.background_label.setMovie(self.movie)
        self.movie.start()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.appbar = AppBar(self)
        self.layout.addWidget(self.appbar)
        self.widgets = []
        self.show_main_screen()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.movie.setScaledSize(self.size())

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowNoState:
                QTimer.singleShot(50, self.showFullScreen)

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
        <span style='color:#008aff;'> </span>
        <span style='color:#008aff;'>A</span>
        <span style='color:#008aff;'>I</span>
        """)
        self.logo_label.setTextFormat(Qt.RichText)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 80, QFont.Bold))
        self.layout.addWidget(self.logo_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(40)
        button_layout.setContentsMargins(60, 20, 60, 20)

        self.btn_edit = QPushButton("Edit Commands")
        self.btn_edit.setCursor(Qt.PointingHandCursor)
        self.btn_edit.setMinimumHeight(120)
        self.btn_recognize = QPushButton("Start Recognition")
        self.btn_recognize.setCursor(Qt.PointingHandCursor)
        self.btn_recognize.setMinimumHeight(120)

        btn_style = """
            QPushButton {
                background-color: #324AB2;
                color: #00FFFF;
                font-size: 20px;
                font-weight: bold;
                border-radius: 16px;
                padding: 15px 30px;
            }
            QPushButton:hover {
                background-color: #324AB2;
                color: white;
            }
        """
        for btn in (self.btn_edit, self.btn_recognize):
            btn.setStyleSheet(btn_style)

        button_layout.addWidget(self.btn_edit)
        button_layout.addWidget(self.btn_recognize)
        self.layout.addLayout(button_layout)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: yellow; font-size: 16px; margin-top: 20px;")
        self.layout.addWidget(self.status_label)

        self.btn_edit.clicked.connect(self.show_edit_labels_ui)
        self.btn_recognize.clicked.connect(lambda: self.run_script("recognize_gesture.py", detached=True))

        self.widgets = [self.logo_label, self.btn_edit, self.btn_recognize, self.status_label]

    def show_message_popup(self, title, message, parent=None):
        if parent is None:
            parent = self
        popup = QDialog(parent)
        popup.setWindowTitle(title)
        popup.setModal(True)
        popup.setFixedSize(420, 180)
        popup.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(15, 15, 15, 15)
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("font-size: 14px;")
        layout.addWidget(lbl)
        btn = QPushButton("OK")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(36)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #00FFFF;
                color: black;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #00d4ff; }
        """)
        btn.clicked.connect(popup.accept)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        popup.exec_()

    def show_edit_labels_ui(self):
        try:
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            LABEL_PATH = os.path.join(BASE_DIR, "models", "gesture_labels.npy")
            if not os.path.exists(LABEL_PATH):
                self.show_message_popup("Error", f"gesture_labels.npy not found at:\n{LABEL_PATH}")
                return
            labels = np.load(LABEL_PATH, allow_pickle=True)
            if len(labels) == 0:
                self.show_message_popup("Warning", "gesture_labels.npy is empty!")
                return

            valid_commands = ["play", "pause", "next", "previous", "mute",
                            "volume_25", "volume_50", "volume_75", "volume_100"]

            gesture_names = [
                "dislike", "four", "like", "mute", "no_gesture", "ok", "one", "fist",
                "peace", "peace_inverted", "palm", "rock", "call", "stop",
                "stop_inverted", "three", "three2", "two_up", "two_up_inverted"
            ]

            popup = QDialog(self)
            popup.setWindowTitle("Edit Commands")
            popup.setStyleSheet("background-color: white; color: black;")
            popup.setModal(True)
            popup.setFixedSize(680, 620)
            layout = QVBoxLayout(popup)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            # --- Valid commands label (moved above table) ---
            valid_lbl_title = QLabel("Valid commands (required):")
            valid_lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
            layout.addWidget(valid_lbl_title)
            valid_text = QLabel(", ".join(valid_commands))
            valid_text.setWordWrap(True)
            valid_text.setStyleSheet("font-size: 13px; color: #444; margin-bottom: 15px;")
            layout.addWidget(valid_text)

            # --- Table header ---
            header_row = QHBoxLayout()
            header_row.setContentsMargins(5,5,5,5)
            header_row.setSpacing(10)

            gesture_hdr = QLabel("Gesture")
            gesture_hdr.setStyleSheet("font-weight: bold; font-size: 15px; background-color:#e0f7fa; padding:5px; border-radius:4px;")
            gesture_hdr.setFixedWidth(200)
            gesture_hdr.setAlignment(Qt.AlignCenter)

            label_hdr = QLabel("Current Command")
            label_hdr.setStyleSheet("font-weight: bold; font-size: 15px; background-color:#e0f7fa; padding:5px; border-radius:4px;")
            label_hdr.setFixedWidth(220)
            label_hdr.setAlignment(Qt.AlignCenter)

            edit_hdr = QLabel("New Command")
            edit_hdr.setStyleSheet("font-weight: bold; font-size: 15px; background-color:#e0f7fa; padding:5px; border-radius:4px;")
            edit_hdr.setAlignment(Qt.AlignCenter)

            header_row.addStretch()
            header_row.addWidget(gesture_hdr)
            header_row.addWidget(label_hdr)
            header_row.addWidget(edit_hdr)
            header_row.addStretch()
            layout.addLayout(header_row)

            # --- Scroll area ---
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(8)
            scroll_layout.setContentsMargins(5,5,5,5)

            self.label_inputs = []

            for i, old_label in enumerate(labels):
                row = QHBoxLayout()
                row.setSpacing(10)
                row.setContentsMargins(2,2,2,2)

                gesture_lbl = QLabel(gesture_names[i] if i < len(gesture_names) else "unknown")
                gesture_lbl.setFixedWidth(200)
                gesture_lbl.setAlignment(Qt.AlignCenter)
                gesture_lbl.setStyleSheet("font-size: 15px; color: #444; background-color:#f0f0f0; padding:4px; border-radius:4px;")

                lbl = QLabel(str(old_label))
                lbl.setStyleSheet("font-weight: bold; font-size: 16px; background-color:#f0f0f0; padding:4px; border-radius:4px;")
                lbl.setFixedWidth(220)
                lbl.setAlignment(Qt.AlignCenter)

                inp = QLineEdit()
                inp.setPlaceholderText("New name (leave blank to keep)")
                inp.setStyleSheet("font-size: 16px; padding: 5px; background-color:#f9f9f9; border:1px solid #ccc; border-radius:4px; color: black;")

                row.addStretch()
                row.addWidget(gesture_lbl)
                row.addWidget(lbl)
                row.addWidget(inp)
                row.addStretch()

                scroll_layout.addLayout(row)
                self.label_inputs.append((old_label, inp))

            scroll_widget.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_widget)
            layout.addWidget(scroll_area)

            btn_save = QPushButton("Save Changes")
            btn_save.setCursor(Qt.PointingHandCursor)
            btn_save.setStyleSheet("""
                QPushButton {
                    background-color: #00FFFF;
                    color: black;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 10px 20px;
                }
                QPushButton:hover { background-color: #00d4ff; }
            """)
            btn_save.clicked.connect(lambda: self.save_label_edits(LABEL_PATH, popup, valid_commands))
            layout.addWidget(btn_save, alignment=Qt.AlignCenter)

            popup.exec_()
        except Exception as e:
            traceback.print_exc()
            self.show_message_popup("Error", f"Exception:\n{str(e)}")


    def save_label_edits(self, path, popup, valid_commands):
        try:
            new_labels = []
            for old, inp in self.label_inputs:
                val = inp.text().strip()
                final = old if val == "" else val
                new_labels.append(str(final))
            normalized = [l.strip() for l in new_labels]
            lowered = [l.lower() for l in normalized]
            duplicates = [x for i, x in enumerate(lowered) if x in lowered[:i]]
            if duplicates:
                self.show_message_popup("Duplicates not allowed", "Please remove duplicate entries.")
                return
            invalid_inputs = []
            for old, inp in self.label_inputs:
                val = inp.text().strip()
                if val != "" and val.lower() not in [vc.lower() for vc in valid_commands]:
                    invalid_inputs.append(val)
            if invalid_inputs:
                self.show_message_popup("Invalid input", "These inputs are invalid:\n" + ", ".join(invalid_inputs))
                return
            final_set = set([l.lower() for l in normalized])
            missing = [vc for vc in valid_commands if vc.lower() not in final_set]
            if missing:
                self.show_message_popup("Missing required commands", "Missing:\n" + ", ".join(missing))
                return
            np.save(path, np.array(normalized, dtype=object))
            popup.accept()
            self.show_message_popup("Saved", "gesture_labels.npy updated successfully!")
            self.show_main_screen()
        except Exception as e:
            traceback.print_exc()
            self.show_message_popup("Error", f"Failed to save labels:\n{str(e)}")

    def run_script_with_popup(self, script, args=None):
        if args is None:
            args = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "gesture_scripts", script)
        if not os.path.exists(script_path):
            self.show_message_popup("Error", f"Script not found:\n{script_path}")
            return
        working_dir = os.path.dirname(script_path)
        popup = QDialog(self)
        popup.setWindowTitle("Reset Progress")
        popup.setModal(True)
        popup.setFixedSize(500, 400)
        popup.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-size: 14px; color: black; background-color: white;")
        layout.addWidget(text_edit)
        progress_bar = QProgressBar()
        progress_bar.setMinimum(0)
        progress_bar.setMaximum(100)
        progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid gray;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk { background-color: #00d4ff; width: 20px; }
        """)
        layout.addWidget(progress_bar)
        popup.show()
        process = QProcess(popup)
        process.setWorkingDirectory(working_dir)
        process.setProcessChannelMode(QProcess.MergedChannels)
        def append_output():
            output = bytes(process.readAllStandardOutput()).decode("utf-8")
            if output.strip():
                text_edit.append(output)
                text_edit.verticalScrollBar().setValue(text_edit.verticalScrollBar().maximum())
                match = re.search(r"PROGRESS:(\d+)", output)
                if match:
                    progress_bar.setValue(int(match.group(1)))
        def process_finished():
            text_edit.append("\nProcess finished!")
            progress_bar.setValue(100)
            QTimer.singleShot(1500, popup.accept)
        process.readyReadStandardOutput.connect(append_output)
        process.finished.connect(process_finished)
        process.start(sys.executable, [script_path] + args)

    def run_script(self, script, args=None, detached=False):
        if args is None:
            args = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_dir, "gesture_scripts", script)
        if not os.path.exists(script_path):
            self.show_message_popup("Error", f"Script not found:\n{script_path}")
            return
        working_dir = os.path.dirname(script_path)
        if detached:
            QProcess.startDetached(sys.executable, [script_path] + args, working_dir)
        else:
            process = QProcess(self)
            process.setWorkingDirectory(working_dir)
            process.start(sys.executable, [script_path] + args)

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/calira_icon.png"))
    def launch_main():
        window = GestureUI()
        window.show()
    intro = IntroScreen()
    intro.start(launch_main)
    sys.exit(app.exec_())
