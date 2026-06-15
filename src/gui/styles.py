"""Application styles and theme (light, UniFi-inspired)."""
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

# Palette (UniFi-like light)
#   accent  #006fff   accent-soft bg #eaf2ff   text #1b1d21   muted #6b7280
#   border  #e6e8eb   panel #ffffff            base #f5f6f8
DARK_THEME = """
QMainWindow, QDialog {
    background-color: #ffffff;
    color: #1b1d21;
}
QWidget {
    background-color: transparent;
    color: #1b1d21;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

/* ---------- Collapsible left sidebar ---------- */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #ececf0;
}
QPushButton#navToggle {
    background-color: transparent;
    border: none;
    border-radius: 9px;
    padding: 9px;
    text-align: center;
}
QPushButton#navToggle:hover { background-color: #f1f3f6; }
QPushButton#navButton {
    text-align: left;
    padding: 9px 11px;
    border: none;
    border-radius: 9px;
    background-color: transparent;
    color: #5a6069;
    font-size: 13px;
    font-weight: 500;
    min-height: 22px;
}
QPushButton#navButton[collapsed="true"] {
    text-align: center;
    padding: 9px;
}
QPushButton#navButton:hover { background-color: #f3f5f8; color: #1b1d21; }
QPushButton#navButton:checked {
    background-color: #eaf2ff;
    color: #0559c9;
    font-weight: 600;
}

/* ---------- Content ---------- */
#content { background-color: #ffffff; }

/* ---------- Collapsible sections (stacked console logs) ---------- */
QPushButton#collapseHeader {
    text-align: left;
    border: none;
    background-color: transparent;
    color: #1b1d21;
    font-size: 14px;
    font-weight: 700;
    padding: 4px 2px;
}
QPushButton#collapseHeader:hover { color: #006fff; }

/* ---------- Flat sections (all-white, hairline dividers) ---------- */
QGroupBox {
    border: none;
    margin-top: 22px;
    padding-top: 4px;
    background-color: transparent;
    font-weight: 700;
    font-size: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 2px;
    padding: 0;
    color: #1b1d21;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: #ffffff;
    color: #33363b;
    border: 1px solid #d6d9de;
    border-radius: 9px;
    padding: 8px 16px;
    min-height: 18px;
}
QPushButton:hover { background-color: #f3f4f6; }
QPushButton:pressed { background-color: #e9ebee; }
QPushButton:disabled { color: #b3b8bf; background-color: #f7f8fa; border-color: #ececf0; }
QPushButton#primaryBtn {
    background-color: #006fff;
    color: #ffffff;
    border: none;
    font-weight: 600;
}
QPushButton#primaryBtn:hover { background-color: #2186ff; }
QPushButton#primaryBtn:pressed { background-color: #0a62db; }
QPushButton#dangerBtn {
    background-color: #ffffff;
    color: #d92d20;
    border: 1px solid #f3c6c2;
    font-weight: 600;
}
QPushButton#dangerBtn:hover { background-color: #fdecea; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #d6d9de;
    border-radius: 8px;
    padding: 6px 9px;
    color: #1b1d21;
    selection-background-color: #006fff;
    selection-color: #ffffff;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 1px solid #006fff; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
    background-color: #f7f8fa; color: #aeb3ba;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e6e8eb;
    border-radius: 8px;
    selection-background-color: #eaf2ff;
    selection-color: #0559c9;
    outline: none;
}

/* ---------- Checkboxes ---------- */
QCheckBox { spacing: 8px; color: #33363b; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid #c8ccd2;
    border-radius: 5px;
    background-color: #ffffff;
}
QCheckBox::indicator:hover { border: 1px solid #006fff; }
QCheckBox::indicator:checked {
    background-color: #006fff;
    border: 1px solid #006fff;
    image: url(__CHECK_IMAGE__);
}

/* ---------- Tables / lists ---------- */
QTableWidget, QListWidget {
    background-color: #ffffff;
    border: none;
    border-top: 1px solid #ececf0;
    border-bottom: 1px solid #ececf0;
    gridline-color: #f1f2f4;
    outline: none;
}
QTableWidget {
    alternate-background-color: #fafbfc;
}
QTableWidget::item, QListWidget::item { padding: 6px 8px; color: #2a2d31; }
QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #eaf2ff;
    color: #0559c9;
}
QListWidget::item { border-radius: 7px; }
QHeaderView::section {
    background-color: #ffffff;
    color: #6b7280;
    border: none;
    border-bottom: 1px solid #ececf0;
    padding: 8px 6px;
    font-weight: 600;
}
QTableCornerButton::section { background-color: #ffffff; border: none; }

/* ---------- Text / log ---------- */
QTextEdit, QPlainTextEdit {
    background-color: #fbfbfc;
    color: #33363b;
    border: 1px solid #e6e8eb;
    border-radius: 12px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 12px;
    padding: 6px;
    selection-background-color: #006fff;
    selection-color: #ffffff;
}

/* ---------- Progress ---------- */
QProgressBar {
    border: none;
    border-radius: 7px;
    background-color: #eceef1;
    text-align: center;
    color: #4b5057;
    height: 16px;
    font-size: 11px;
}
QProgressBar::chunk { background-color: #006fff; border-radius: 7px; }
QProgressBar#cpuBar::chunk { background-color: #2e9e5b; border-radius: 7px; }

/* ---------- Sliders (video timeline) ---------- */
QSlider::groove:horizontal { height: 4px; background: #e1e4e8; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #006fff; border-radius: 2px; }
QSlider::handle:horizontal {
    background: #ffffff; border: 1px solid #c2c7ce;
    width: 14px; height: 14px; margin: -6px 0; border-radius: 7px;
}
QSlider::handle:horizontal:hover { border: 1px solid #006fff; }

/* ---------- Scrollbars ---------- */
QScrollBar:vertical { background: transparent; width: 11px; margin: 2px; }
QScrollBar::handle:vertical { background: #cdd2d8; border-radius: 5px; min-height: 28px; }
QScrollBar::handle:vertical:hover { background: #b6bcc4; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 11px; margin: 2px; }
QScrollBar::handle:horizontal { background: #cdd2d8; border-radius: 5px; min-width: 28px; }
QScrollBar::handle:horizontal:hover { background: #b6bcc4; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ---------- Tabs (legacy; unused) ---------- */
QTabWidget::pane { border: none; }

/* ---------- Splitter ---------- */
QSplitter::handle { background-color: #ececf0; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }

/* ---------- Menus ---------- */
QMenuBar { background-color: #ffffff; color: #33363b; border-bottom: 1px solid #ececf0; }
QMenuBar::item { padding: 6px 10px; background: transparent; }
QMenuBar::item:selected { background-color: #f1f3f6; border-radius: 6px; }
QMenu {
    background-color: #ffffff;
    color: #1b1d21;
    border: 1px solid #e6e8eb;
    border-radius: 10px;
    padding: 6px;
}
QMenu::item { padding: 7px 18px; border-radius: 7px; }
QMenu::item:selected { background-color: #eaf2ff; color: #0559c9; }
QMenu::separator { height: 1px; background: #ececf0; margin: 5px 8px; }

/* ---------- Status bar / tooltip ---------- */
QStatusBar { background-color: #ffffff; color: #6b7280; border-top: 1px solid #ececf0; }
QToolTip {
    background-color: #1b1d21;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 5px 8px;
}

/* ---------- Menu-bar popover ---------- */
#popoverWindow { background: transparent; }
#popoverCard {
    background-color: #ffffff;
    border: 1px solid #e3e6ea;
    border-radius: 18px;
}
#popoverTitle { font-size: 15px; font-weight: 700; color: #1b1d21; }
#popoverSub { color: #9aa0a8; font-size: 11px; }
#popoverStatus { color: #6b7280; font-size: 12px; padding: 0 2px; }
#popoverRow {
    background-color: #ffffff;
    border: 1px solid #ececf0;
    border-radius: 14px;
}
#popoverRow:hover { background-color: #fafbfc; }
#popoverRowTitle { font-weight: 600; color: #1b1d21; font-size: 13px; }
#popoverRowSub { color: #9aa0a8; font-size: 11px; }
#popoverGhost { background-color: transparent; border: none; border-radius: 16px; }
#popoverGhost:hover { background-color: #f1f3f6; }
""".replace("__CHECK_IMAGE__", _CHECK_IMAGE_PATH) \
   .replace('"Segoe UI", Arial, sans-serif', _UI_FONT) \
   .replace('"Cascadia Code", "Consolas", monospace', _MONO_FONT)
