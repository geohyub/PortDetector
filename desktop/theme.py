"""
PortDetector PySide6 theme — thin re-export wrapper over GeoView shared design system.

All standard design tokens (colors, typography, spacing) are sourced from
geoview_pyside6.constants.  App-specific values (device status colors, sidebar
palette, monospace font) are kept here.

Migration note (2026-04-04):
  Colors -> Dark + DeviceColors + app-specific aliases
  Fonts  -> Font + app-specific sizes
  STYLESHEET -> kept locally (PortDetector uses its own MainWindow)
"""

import sys
from pathlib import Path

# ── Shared design system import ────────────────────────────────────────────
_shared = str(Path(__file__).resolve().parents[3] / "_shared")
if _shared not in sys.path:
    sys.path.insert(0, _shared)

from geoview_pyside6.constants import (  # noqa: F401
    Dark, Font, Space, Radius, Opacity, DeviceColors,
)


# ── Color Palette — aliases to shared constants + app-specific extras ──────
class Colors:
    """Color constants — dark theme with cyan accent + device status colors.

    Standard tokens delegate to ``Dark`` and ``DeviceColors``; app-specific
    values are defined inline.  New code should import ``Dark`` / ``DeviceColors``
    directly.
    """

    # Base — sourced from Dark
    BG       = Dark.BG
    BG_CARD  = Dark.NAVY
    BG_INPUT = Dark.DARK
    BG_ALT   = Dark.BG_ALT

    # Borders — app-specific (PortDetector uses purple-tinted borders)
    BORDER       = "#2a2a4a"
    BORDER_LIGHT = "#3a3a5a"

    # Text — app-specific (PortDetector uses slightly different text tones)
    TEXT       = "#e0e0e0"
    TEXT_DIM   = "#8888aa"
    TEXT_MUTED = "#6a6a8a"

    # Accent — sourced from Dark
    ACCENT       = Dark.CYAN
    ACCENT_HOVER = "#0096c7"                       # app-specific
    ACCENT_DIM   = f"{Dark.CYAN}{Opacity.LOW}"     # 10% opacity

    # Device status — sourced from DeviceColors
    CONNECTED        = DeviceColors.CONNECTED
    CONNECTED_DIM    = f"{DeviceColors.CONNECTED}{Opacity.LOW}"
    DISCONNECTED     = DeviceColors.DISCONNECTED
    DISCONNECTED_DIM = f"{DeviceColors.DISCONNECTED}{Opacity.LOW}"
    DELAYED          = DeviceColors.DELAYED
    DELAYED_DIM      = f"{DeviceColors.DELAYED}{Opacity.LOW}"

    # Port status — sourced from DeviceColors
    OPEN     = DeviceColors.CONNECTED
    CLOSED   = DeviceColors.DISCONNECTED
    FILTERED = DeviceColors.FILTERED

    # Sidebar — app-specific (dark indigo sidebar)
    SIDEBAR_BG            = "#111128"
    SIDEBAR_HOVER         = "#1a1a3e"
    SIDEBAR_ACTIVE        = f"{Dark.CYAN}20"       # 12% opacity
    SIDEBAR_ACTIVE_BORDER = Dark.CYAN

    # Semantic status — sourced from DeviceColors
    DANGER  = DeviceColors.DISCONNECTED
    WARNING = DeviceColors.DELAYED
    SUCCESS = DeviceColors.CONNECTED
    INFO    = Dark.CYAN


# ── Font constants — aliases to shared Font + app-specific extras ──────────
class Fonts:
    """Font sizes and families.

    Standard tokens delegate to ``Font``; app-specific sizes are defined
    inline.  New code should import ``Font`` directly.
    """

    FAMILY     = Font.SANS      # "Pretendard"
    MONO       = "Cascadia Code"  # app-specific monospace
    SIZE_XS    = 12             # app-specific (between Font.XS 11 and Font.SM 13)
    SIZE_SM    = Font.SM        # 13
    SIZE_MD    = Font.BASE      # 14
    SIZE_LG    = 16             # app-specific (Font.MD is 15)
    SIZE_XL    = 20             # app-specific (between Font.LG 17 and Font.XL 22)
    SIZE_TITLE = Font.XXL       # 26


# ── Stylesheet ──────────────────────────────────────────────────────────────
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
    font-weight: {Font.MEDIUM};
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
    font-weight: {Font.SEMIBOLD};
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
    border-radius: {Radius.SM}px;
}}
.device-card:hover {{
    border-color: {Colors.BORDER_LIGHT};
}}

/* Tables */
QTableWidget {{
    background-color: {Colors.BG};
    border: none;
    gridline-color: transparent;
    font-family: "{Fonts.FAMILY}", "Segoe UI";
    font-size: {Fonts.SIZE_SM}px;
}}
QTableWidget::item {{
    padding: 5px 8px;
    border-bottom: 1px solid {Colors.BORDER};
    font-family: "{Fonts.FAMILY}", "Segoe UI";
    font-size: {Fonts.SIZE_SM}px;
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
    font-family: "{Fonts.FAMILY}", "Segoe UI";
    font-size: {Fonts.SIZE_SM}px;
    font-weight: {Font.MEDIUM};
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
    font-weight: {Font.MEDIUM};
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
    font-weight: {Font.MEDIUM};
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
