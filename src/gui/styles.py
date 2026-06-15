"""Application styles and theme."""
import os

from src.utils import platform_utils

_STYLE_DIR = os.path.dirname(os.path.abspath(__file__))
_CHECK_IMAGE_PATH = os.path.join(_STYLE_DIR, "check.svg").replace("\\", "/")

# Lead each font stack with a family that exists on the current platform, so Qt
# doesn't warn about (and waste time aliasing) missing families like "Segoe UI".
if platform_utils.IS_MACOS:
    _UI_FONT = '"Helvetica Neue", "Arial", sans-serif'
    _MONO_FONT = '"Menlo", "SF Mono", "Monaco", monospace'
elif platform_utils.IS_WINDOWS:
    _UI_FONT = '"Segoe UI", "Arial", sans-serif'
    _MONO_FONT = '"Cascadia Code", "Consolas", monospace'
else:
    _UI_FONT = '"Noto Sans", "DejaVu Sans", "Arial", sans-serif'
    _MONO_FONT = '"DejaVu Sans Mono", "Liberation Mono", monospace'

DARK_THEME = """
QMainWindow, QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QPushButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 5px;
    padding: 6px 16px;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #585b70;
    border-color: #89b4fa;
}
QPushButton:pressed {
    background-color: #313244;
}
QPushButton:disabled {
    background-color: #313244;
    color: #6c7086;
}
QPushButton#primaryBtn {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}
QPushButton#primaryBtn:hover {
    background-color: #b4d0fb;
}
QPushButton#primaryBtn:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}
QPushButton#dangerBtn:hover {
    background-color: #f5a6bc;
}
QPushButton#successBtn {
    background-color: #a6e3a1;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}
QPushButton#successBtn:hover {
    background-color: #b8eab4;
}
QLineEdit, QSpinBox, QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 8px;
    min-height: 22px;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #89b4fa;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #cdd6f4;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
}
QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #45475a;
    border-radius: 3px;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
    image: url(__CHECK_IMAGE__);
}
QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 4px;
    background-color: #1e1e2e;
}
QTabBar::tab {
    background-color: #313244;
    color: #a6adc8;
    padding: 8px 20px;
    border: 1px solid #45475a;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #1e1e2e;
    color: #89b4fa;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #45475a;
}
QTableWidget, QTreeWidget, QListWidget {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    gridline-color: #313244;
    alternate-background-color: #1e1e2e;
}
QTableWidget::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #45475a;
}
QHeaderView::section {
    background-color: #313244;
    color: #89b4fa;
    padding: 6px;
    border: none;
    border-right: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
    font-weight: bold;
}
QTextEdit, QPlainTextEdit {
    background-color: #11111b;
    color: #a6e3a1;
    border: 1px solid #45475a;
    border-radius: 4px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 4px;
}
QProgressBar {
    border: 1px solid #45475a;
    border-radius: 4px;
    text-align: center;
    background-color: #313244;
    color: #cdd6f4;
    min-height: 20px;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 3px;
}
QProgressBar#cpuBar {
    min-height: 16px;
    font-size: 11px;
    color: #f5c2d0;
}
QProgressBar#cpuBar::chunk {
    background-color: #a04058;
    border-radius: 3px;
}
QScrollBar:vertical {
    background-color: #181825;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #45475a;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585b70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background-color: #181825;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #45475a;
    border-radius: 5px;
    min-width: 30px;
}
QSplitter::handle {
    background-color: #45475a;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #89b4fa;
}
QLabel#subtitleLabel {
    font-size: 11px;
    color: #6c7086;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #45475a;
}
QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #45475a;
}
QMenuBar::item:selected {
    background-color: #45475a;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
}
QMenu::item:selected {
    background-color: #45475a;
}
QToolTip {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    padding: 4px;
}

/* ===================== Revamped sidebar UI ===================== */
#sidebar {
    background-color: #13131c;
    border-right: 1px solid #26263a;
}
#brandLabel {
    color: #cdd6f4;
    font-size: 17px;
    font-weight: 700;
    padding: 0 4px;
}
#brandVersion {
    color: #6c7086;
    font-size: 11px;
    padding: 0 4px;
}
#sidebarCaption {
    color: #6c7086;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 4px;
}
#sidebarSep {
    color: #26263a;
    background-color: #26263a;
    max-height: 1px;
    border: none;
}
QPushButton#navButton {
    text-align: left;
    padding: 10px 12px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 8px;
    background-color: transparent;
    color: #a6adc8;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background-color: #1c1c2a;
    color: #cdd6f4;
}
QPushButton#navButton:checked {
    background-color: #232336;
    color: #ffffff;
    border-left: 3px solid #89b4fa;
    font-weight: 600;
}
#content {
    background-color: #1e1e2e;
}

/* ===================== Modern polish ===================== */
QGroupBox {
    border: 1px solid #2a2a3c;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 8px;
    background-color: #1b1b29;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #3a3a4e;
    border-radius: 8px;
    padding: 7px 14px;
}
QPushButton:hover { background-color: #3a3a4e; }
QPushButton:pressed { background-color: #45475a; }
QPushButton:disabled { color: #6c7086; background-color: #242436; border-color: #2a2a3c; }
QPushButton#primaryBtn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #9ec1fb; }
QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
    font-weight: 600;
}
QPushButton#dangerBtn:hover { background-color: #f5a0b8; }
QLineEdit, QComboBox, QSpinBox {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 6px 8px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #89b4fa; }
QTableWidget, QListWidget {
    background-color: #181825;
    border: 1px solid #2a2a3c;
    border-radius: 10px;
    gridline-color: #26263a;
}
QHeaderView::section {
    background-color: #1b1b29;
    color: #a6adc8;
    border: none;
    border-bottom: 1px solid #2a2a3c;
    padding: 7px 6px;
    font-weight: 600;
}
QListWidget::item { padding: 7px 8px; border-radius: 6px; }
QListWidget::item:selected, QTableWidget::item:selected {
    background-color: #313244;
    color: #ffffff;
}
QProgressBar {
    border: none;
    border-radius: 6px;
    background-color: #26263a;
    text-align: center;
    color: #cdd6f4;
    height: 16px;
    font-size: 11px;
}
QProgressBar::chunk { background-color: #89b4fa; border-radius: 6px; }
QProgressBar#cpuBar::chunk { background-color: #a6e3a1; border-radius: 6px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #45475a; border-radius: 5px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal { background: #45475a; border-radius: 5px; min-width: 28px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ===================== Mac glass / minimalist refinement ===================== */
#content {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #20202f, stop:1 #16161e);
}
#sidebar {
    background-color: rgba(14, 14, 20, 0.92);
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}
QGroupBox {
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    margin-top: 16px;
    padding-top: 10px;
    background-color: rgba(255, 255, 255, 0.04);
}
QGroupBox::title { color: #89b4fa; left: 14px; }
QPushButton {
    border-radius: 11px;
    padding: 8px 16px;
    background-color: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #cdd6f4;
}
QPushButton:hover { background-color: rgba(255, 255, 255, 0.12); }
QPushButton:pressed { background-color: rgba(255, 255, 255, 0.16); }
QPushButton:disabled { background-color: rgba(255, 255, 255, 0.03); color: #6c7086;
    border-color: rgba(255, 255, 255, 0.05); }
QPushButton#primaryBtn { background-color: #89b4fa; border: none; color: #0b1020; font-weight: 600; }
QPushButton#primaryBtn:hover { background-color: #a6c8ff; }
QPushButton#dangerBtn { background-color: #f38ba8; border: none; color: #2a0e16; font-weight: 600; }
QPushButton#dangerBtn:hover { background-color: #f7a3bb; }
QPushButton#navButton {
    border-radius: 10px;
    padding: 11px 12px;
    border-left: 3px solid transparent;
    background-color: transparent;
}
QPushButton#navButton:hover { background-color: rgba(255, 255, 255, 0.06); }
QPushButton#navButton:checked {
    background-color: rgba(137, 180, 250, 0.16);
    border-left: 3px solid #89b4fa;
    color: #ffffff;
}
QLineEdit, QComboBox, QSpinBox {
    border-radius: 10px;
    padding: 8px 10px;
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #cdd6f4;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 1px solid #89b4fa;
    background-color: rgba(255, 255, 255, 0.08);
}
QTableWidget, QListWidget {
    border-radius: 14px;
    background-color: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
}
QHeaderView::section {
    background-color: transparent;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding: 8px 6px;
    color: #a6adc8;
}
QTextEdit, QPlainTextEdit { border-radius: 14px; border: 1px solid rgba(255,255,255,0.07); }
QProgressBar { border-radius: 8px; background-color: rgba(255, 255, 255, 0.08); }
QProgressBar::chunk { border-radius: 8px; }
QMenu {
    background-color: #20202e;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
    padding: 6px;
}
QMenu::item { padding: 7px 18px; border-radius: 7px; }
QMenu::item:selected { background-color: rgba(137, 180, 250, 0.20); }
QMenu::separator { height: 1px; background: rgba(255,255,255,0.08); margin: 5px 8px; }
""".replace("__CHECK_IMAGE__", _CHECK_IMAGE_PATH) \
   .replace('"Segoe UI", Arial, sans-serif', _UI_FONT) \
   .replace('"Cascadia Code", "Consolas", monospace', _MONO_FONT)
