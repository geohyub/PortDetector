"""PortDetector PySide6 theme — dark theme, colors, fonts, stylesheet."""


class Colors:
    # Base
    BG = "#1a1a2e"
    BG_CARD = "#16213e"
    BG_INPUT = "#0f3460"
    BG_ALT = "#1c2541"
    BORDER = "#2a2a4a"
    BORDER_LIGHT = "#3a3a5a"

    # Text
    TEXT = "#e0e0e0"
    TEXT_DIM = "#8888aa"
    TEXT_MUTED = "#6a6a8a"

    # Accent
    ACCENT = "#00b4d8"
    ACCENT_HOVER = "#0096c7"
    ACCENT_DIM = "#00b4d81a"

    # Status
    CONNECTED = "#06d6a0"
    CONNECTED_DIM = "#06d6a01a"
    DISCONNECTED = "#ef476f"
    DISCONNECTED_DIM = "#ef476f1a"
    DELAYED = "#ffd166"
    DELAYED_DIM = "#ffd1661a"

    # Ports
    OPEN = "#06d6a0"
    CLOSED = "#ef476f"
    FILTERED = "#ffd166"

    # Sidebar
    SIDEBAR_BG = "#111128"
    SIDEBAR_HOVER = "#1a1a3e"
    SIDEBAR_ACTIVE = "#00b4d820"
    SIDEBAR_ACTIVE_BORDER = "#00b4d8"

    # Misc
    DANGER = "#ef476f"
    WARNING = "#ffd166"
    SUCCESS = "#06d6a0"
    INFO = "#00b4d8"


class Fonts:
    FAMILY = "Pretendard"
    MONO = "Cascadia Code"
    SIZE_XS = 10
    SIZE_SM = 11
    SIZE_MD = 12
    SIZE_LG = 14
    SIZE_XL = 18
    SIZE_TITLE = 24


STYLESHEET = f"""
QWidget {{
    background-color: {Colors.BG};
    color: {Colors.TEXT};
    font-family: "{Fonts.FAMILY}", "Segoe UI";
    font-size: {Fonts.SIZE_MD}px;
}}

/* Sidebar */
#sidebar {{
    background-color: {Colors.SIDEBAR_BG};
    border-right: 1px solid {Colors.BORDER};
    min-width: 200px;
    max-width: 200px;
}}
#sidebar QPushButton {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    color: {Colors.TEXT_DIM};
    font-size: {Fonts.SIZE_MD}px;
    padding: 10px 16px;
    text-align: left;
}}
#sidebar QPushButton:hover {{
    background-color: {Colors.SIDEBAR_HOVER};
    color: {Colors.TEXT};
}}
#sidebar QPushButton[active="true"] {{
    background-color: {Colors.SIDEBAR_ACTIVE};
    border-left: 3px solid {Colors.SIDEBAR_ACTIVE_BORDER};
    color: {Colors.ACCENT};
    font-weight: 500;
}}

/* Top Bar */
#topbar {{
    background-color: {Colors.SIDEBAR_BG};
    border-bottom: 1px solid {Colors.BORDER};
    min-height: 48px;
    max-height: 48px;
}}
#topbar QLabel {{
    background: transparent;
}}
#topbar_title {{
    font-size: {Fonts.SIZE_LG}px;
    font-weight: 600;
    color: {Colors.TEXT};
}}
#topbar_version {{
    font-size: {Fonts.SIZE_XS}px;
    color: {Colors.TEXT_MUTED};
}}

/* Cards */
.device-card {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
}}
.device-card:hover {{
    border-color: {Colors.BORDER_LIGHT};
}}

/* Tables */
QTableWidget {{
    background-color: {Colors.BG};
    border: none;
    gridline-color: transparent;
    font-size: {Fonts.SIZE_SM}px;
}}
QTableWidget::item {{
    padding: 4px 8px;
    border-bottom: 1px solid {Colors.BORDER};
}}
QTableWidget::item:selected {{
    background-color: {Colors.ACCENT_DIM};
    color: {Colors.TEXT};
}}
QHeaderView::section {{
    background-color: transparent;
    color: {Colors.TEXT_DIM};
    border: none;
    border-bottom: 1px solid {Colors.BORDER_LIGHT};
    font-size: {Fonts.SIZE_SM}px;
    font-weight: 500;
    padding: 6px 8px;
}}

/* Buttons */
QPushButton {{
    background-color: {Colors.BG_INPUT};
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    color: {Colors.TEXT};
    font-size: {Fonts.SIZE_SM}px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: {Colors.ACCENT_HOVER};
    border-color: {Colors.ACCENT};
}}
QPushButton:pressed {{
    background-color: {Colors.ACCENT};
}}
QPushButton:disabled {{
    background-color: {Colors.BG_ALT};
    color: {Colors.TEXT_MUTED};
    border-color: {Colors.BORDER};
}}
QPushButton#btn_primary {{
    background-color: {Colors.ACCENT};
    border-color: {Colors.ACCENT};
    color: #ffffff;
    font-weight: 500;
}}
QPushButton#btn_primary:hover {{
    background-color: {Colors.ACCENT_HOVER};
}}
QPushButton#btn_danger {{
    background-color: {Colors.DANGER};
    border-color: {Colors.DANGER};
    color: #ffffff;
}}

/* Inputs */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {Colors.BG_INPUT};
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    color: {Colors.TEXT};
    font-size: {Fonts.SIZE_SM}px;
    padding: 5px 8px;
    min-height: 28px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {Colors.ACCENT};
}}

/* Scrollbar */
QScrollBar:vertical {{
    background-color: {Colors.BG};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {Colors.BORDER_LIGHT};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {Colors.TEXT_MUTED};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: {Colors.BG};
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background-color: {Colors.BORDER_LIGHT};
    border-radius: 4px;
    min-width: 30px;
}}

/* Tab widget (for sub-tabs) */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    border-top: none;
}}
QTabBar::tab {{
    background-color: {Colors.BG_ALT};
    border: 1px solid {Colors.BORDER};
    border-bottom: none;
    color: {Colors.TEXT_DIM};
    padding: 6px 16px;
    font-size: {Fonts.SIZE_SM}px;
}}
QTabBar::tab:selected {{
    background-color: {Colors.BG};
    color: {Colors.ACCENT};
    font-weight: 500;
}}

/* Progress bar */
QProgressBar {{
    background-color: {Colors.BG_ALT};
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    height: 18px;
    text-align: center;
    font-size: {Fonts.SIZE_XS}px;
    color: {Colors.TEXT};
}}
QProgressBar::chunk {{
    background-color: {Colors.ACCENT};
    border-radius: 3px;
}}

/* Tooltip */
QToolTip {{
    background-color: {Colors.BG_CARD};
    border: 1px solid {Colors.BORDER};
    color: {Colors.TEXT};
    padding: 4px 8px;
    font-size: {Fonts.SIZE_SM}px;
}}

/* GroupBox */
QGroupBox {{
    border: 1px solid {Colors.BORDER};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-size: {Fonts.SIZE_SM}px;
    color: {Colors.TEXT_DIM};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

/* CheckBox */
QCheckBox {{
    spacing: 6px;
    font-size: {Fonts.SIZE_SM}px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {Colors.BORDER_LIGHT};
    border-radius: 3px;
    background-color: {Colors.BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {Colors.ACCENT};
    border-color: {Colors.ACCENT};
}}
"""
