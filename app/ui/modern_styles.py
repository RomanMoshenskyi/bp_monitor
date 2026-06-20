"""PulseView Design System — Centralized QSS generator and token library."""
from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════
#  Token library (Tailwind-inspired)
# ═══════════════════════════════════════════════════════════════════
class Tokens:
    PRIMARY       = "#6366f1"
    PRIMARY_DARK  = "#4f46e5"
    PRIMARY_LIGHT = "#818cf8"
    VIOLET        = "#8b5cf6"
    VIOLET_DARK   = "#7c3aed"
    PINK          = "#ec4899"
    CYAN          = "#06b6d4"
    SUCCESS       = "#10b981"
    SUCCESS_DARK  = "#059669"
    DANGER        = "#f43f5e"
    DANGER_DARK   = "#e11d48"
    WARNING       = "#f59e0b"
    WARNING_DARK  = "#d97706"
    INFO          = "#06b6d4"
    INFO_DARK     = "#0891b2"

    SLATE_50  = "#f8fafc"
    SLATE_100 = "#f1f5f9"
    SLATE_200 = "#e2e8f0"
    SLATE_300 = "#cbd5e1"
    SLATE_400 = "#94a3b8"
    SLATE_500 = "#64748b"
    SLATE_600 = "#475569"
    SLATE_700 = "#334155"
    SLATE_800 = "#1e293b"
    SLATE_900 = "#0f172a"

    RADIUS_SM  = 10
    RADIUS_MD  = 14
    RADIUS_LG  = 18
    RADIUS_XL  = 24
    RADIUS_2XL = 32

    FONT_UI = "'SF Pro Display', 'Segoe UI Variable Display', 'Segoe UI', 'Inter', system-ui, sans-serif"


def _grad(*stops: str) -> str:
    """Build qlineargradient string."""
    pairs = " ".join(f"stop:{i/(len(stops)-1)} {s}" for i, s in enumerate(stops))
    return f"qlineargradient(x1:0,y1:0,x2:1,y2:1, {pairs})"


def button_style(color: str = "primary", size: str = "md") -> str:
    """Generate premium button QSS."""
    t = Tokens
    palettes = {
        "primary": (t.PRIMARY, t.VIOLET_DARK, t.VIOLET, t.PRIMARY_DARK, "#6d28d9", t.VIOLET_DARK, "#4338ca", "#5b21b6"),
        "success": (t.SUCCESS, t.SUCCESS_DARK, "#047857", "#059669", "#047857", "#065f46", "#064e3b", "#022c22"),
        "danger":  (t.DANGER,  t.DANGER_DARK,  "#be123c", "#e11d48", "#be123c", "#9f1239", "#881337", "#4c0519"),
        "warning": (t.WARNING, t.WARNING_DARK, "#b45309", "#d97706", "#b45309", "#92400e", "#78350f", "#451a03"),
        "info":    (t.INFO,    t.INFO_DARK,    "#0e7490", "#0891b2", "#0e7490", "#155e75", "#164e63", "#083344"),
    }
    c1, c2, c3, h1, h2, h3, p1, p2 = palettes.get(color, palettes["primary"])
    sizes = {
        "sm":  "padding: 6px 14px; font-size: 12px; min-height: 30px;",
        "md":  "padding: 9px 22px; font-size: 13px; min-height: 38px;",
        "lg":  "padding: 12px 28px; font-size: 14px; min-height: 44px;",
    }
    sz = sizes.get(size, sizes["md"])
    return f"""
        QPushButton {{ background: {_grad(c1,c2,c3)}; color: white; border: none;
                      border-radius: {Tokens.RADIUS_MD}px; {sz} font-weight: 700;
                      letter-spacing: 0.2px; font-family: {Tokens.FONT_UI}; }}
        QPushButton:hover {{ background: {_grad(h1,h2,h3)}; }}
        QPushButton:pressed {{ background: {_grad(p1,p2,p2)}; }}
        QPushButton:disabled {{ background: #c7d2fe; color: #e0e7ff; }}
    """


def ghost_button_style(color: str = "primary") -> str:
    t = Tokens
    c = {"primary":t.PRIMARY,"danger":t.DANGER,"success":t.SUCCESS,"warning":t.WARNING,"info":t.INFO}.get(color, t.PRIMARY)
    return f"""
        QPushButton {{ background: transparent; color: {c}; border: 1.5px solid {c}20;
                      border-radius: {t.RADIUS_MD}px; padding: 8px 18px; font-size: 13px;
                      font-weight: 600; font-family: {t.FONT_UI}; }}
        QPushButton:hover {{ background: {c}08; border-color: {c}40; }}
        QPushButton:pressed {{ background: {c}12; }}
    """


def input_style() -> str:
    t = Tokens
    return f"""
        QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateEdit {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafbff,stop:1 #f5f7ff);
            border: 1.5px solid {t.SLATE_200}; border-radius: {t.RADIUS_MD}px;
            padding: 8px 14px; color: {t.SLATE_800}; font-size: 13px;
            min-height: 36px; font-family: {t.FONT_UI};
            selection-background-color: {t.PRIMARY_LIGHT}40;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
            border-color: {t.PRIMARY_LIGHT}; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafaff,stop:1 #f5f3ff);
            outline: none;
        }}
        QLineEdit:hover:!focus, QSpinBox:hover:!focus, QComboBox:hover:!focus, QDateEdit:hover:!focus {{
            border-color: #a5b4fc; background: #fbfcff;
        }}
        QLineEdit::placeholder, QTextEdit::placeholder {{ color: {t.SLATE_400}; font-style: italic; }}
        QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right; width: 28px; border-left: 1px solid {t.SLATE_200}; }}
        QComboBox QAbstractItemView {{ background: #ffffff; border: 1px solid {t.SLATE_200}; border-radius: {t.RADIUS_SM}px; padding: 4px; selection-background-color: {t.PRIMARY_LIGHT}20; }}
        QCalendarWidget {{ background: #ffffff; }}
        QCalendarWidget QTableView {{ background: #ffffff; alternate-background-color: #fafaff; }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth, QCalendarWidget QToolButton#qt_calendar_nextmonth, QCalendarWidget QToolButton#qt_calendar_monthbutton, QCalendarWidget QToolButton#qt_calendar_yearbutton {{ background: #ffffff; color: {t.SLATE_800}; border: none; border-radius: 4px; }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth:hover, QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {{ background: {t.PRIMARY_LIGHT}20; }}
        QCalendarWidget QToolButton#qt_calendar_prevmonth:pressed, QCalendarWidget QToolButton#qt_calendar_nextmonth:pressed {{ background: {t.PRIMARY_LIGHT}40; }}
        QCalendarWidget QSpinBox {{ background: #ffffff; }}
    """


def card_style(bg: str = "#ffffff", border: str = "rgba(226,232,240,0.65)") -> str:
    return f"""
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {bg},stop:1 #fcfcff);
        border: 1.5px solid {border};
        border-radius: {Tokens.RADIUS_LG}px;
        padding: 22px;
    """


def table_style() -> str:
    t = Tokens
    return f"""
        QTableWidget {{
            background: transparent; border: 1.5px solid {t.SLATE_200};
            border-radius: {t.RADIUS_LG}px; gridline-color: {t.SLATE_100};
            font-family: {t.FONT_UI}; font-size: 13px; color: {t.SLATE_700};
        }}
        QTableWidget::item {{ padding: 10px 14px; border-bottom: 1px solid {t.SLATE_100}; }}
        QTableWidget::item:selected {{ background: {t.PRIMARY_LIGHT}18; color: {t.SLATE_900}; }}
        QHeaderView::section {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {t.SLATE_50},stop:1 {t.SLATE_100});
            color: {t.SLATE_600}; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
            padding: 10px 14px; border: none; border-bottom: 1.5px solid {t.SLATE_200};
            text-transform: uppercase;
        }}
        QTableCornerButton::section {{ background: {t.SLATE_50}; border: none; }}
        QTableWidget::item:hover {{ background: {t.SLATE_50}; }}
    """


def scroll_style() -> str:
    t = Tokens
    return f"""
        QScrollBar:vertical {{ background: transparent; width: 8px; margin: 4px; }}
        QScrollBar::handle:vertical {{ background: {t.SLATE_300}; border-radius: 4px; min-height: 32px; }}
        QScrollBar::handle:vertical:hover {{ background: {t.SLATE_400}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
        QScrollBar:horizontal {{ background: transparent; height: 8px; margin: 4px; }}
        QScrollBar::handle:horizontal {{ background: {t.SLATE_300}; border-radius: 4px; min-width: 32px; }}
        QScrollBar::handle:horizontal:hover {{ background: {t.SLATE_400}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
    """


def tab_style() -> str:
    t = Tokens
    return f"""
        QTabWidget::pane {{ border: 1.5px solid {t.SLATE_200}; border-radius: {t.RADIUS_LG}px; background: white; padding: 18px; }}
        QTabBar::tab {{ background: transparent; border: none; border-bottom: 2.5px solid transparent;
                        padding: 10px 24px; margin-right: 6px; color: {t.SLATE_400};
                        font-weight: 600; font-size: 13px; font-family: {t.FONT_UI}; }}
        QTabBar::tab:selected {{ color: {t.PRIMARY}; border-bottom: 3px solid {_grad(t.PRIMARY, t.VIOLET)};
                                 font-weight: 700; }}
        QTabBar::tab:hover:!selected {{ color: {t.PRIMARY}; border-bottom-color: {t.PRIMARY}40; }}
    """


def tooltip_style() -> str:
    return f"""
        QToolTip {{ background: {Tokens.SLATE_800}; color: #ffffff; border: none;
                   border-radius: {Tokens.RADIUS_SM}px; padding: 6px 10px; font-size: 12px; }}
    """


def build_global_stylesheet() -> str:
    """Assemble the complete application stylesheet."""
    t = Tokens
    return f"""
/* ═══════════════════════════════════════════════════════════════
   PulseView 2.0 — Global Premium Stylesheet
   ═══════════════════════════════════════════════════════════════ */

QMainWindow, QWidget {{
    background: qlineargradient(x1:0,y1:0,x2:0.5,y2:1,stop:0 #f0f2ff,stop:0.4 #f5f7ff,stop:1 #eef1fb);
    color: {t.SLATE_800}; font-family: {t.FONT_UI}; font-size: 13px;
}}

/* Sidebar */
QFrame#sidebar {{
    background: qlineargradient(x1:0,y1:0,x2:0.3,y2:1,stop:0 #0a0e27,stop:0.3 #111642,stop:0.65 #1a1260,stop:1 #2a1f7a);
    border-radius: {t.RADIUS_XL}px; border: 1px solid {t.PRIMARY}08;
}}
QFrame#sidebar[collapsed="true"] {{
    background: qlineargradient(x1:0,y1:0,x2:0.3,y2:1,stop:0 #0a0e27,stop:0.3 #111642,stop:0.65 #1a1260,stop:1 #2a1f7a);
    border-radius: {t.RADIUS_LG}px;
}}
QFrame#sidebar QWidget, QFrame#sidebar QLabel {{ background: transparent; }}
QLabel#brandTitle {{
    color: #ffffff; font-size: 22px; font-weight: 800; letter-spacing: 0.5px; background: transparent;
}}
QLabel#brandSubtitle {{
    color: rgba(196,181,253,0.72); font-size: 11px; font-weight: 500; letter-spacing: 0.2px; background: transparent;
}}
QFrame#navDivider {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {t.PRIMARY}00,stop:0.5 {t.VIOLET}40,stop:1 {t.PRIMARY}00);
    max-height: 1px; border: none;
}}
QLabel#navSectionLabel {{
    color: {t.SLATE_400}55; font-size: 9.5px; font-weight: 800; letter-spacing: 1.5px;
    text-transform: uppercase; background: transparent; padding: 0 6px;
}}

/* Nav buttons */
QPushButton#navButton {{
    text-align: left; color: rgba(203,193,255,0.72); background: transparent; border: none;
    padding: 11px 16px; border-radius: {t.RADIUS_MD}px; font-size: 13px; font-weight: 500; letter-spacing: 0.1px;
}}
QPushButton#navButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(255,255,255,0.06),stop:1 rgba(139,92,246,0.06));
    color: rgba(255,255,255,0.95);
}}
QPushButton#navButton:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {t.PRIMARY}45,stop:0.6 {t.VIOLET}30,stop:1 rgba(168,85,247,0.18));
    color: #ffffff; font-weight: 700;
    border-left: 3px solid qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #a78bfa,stop:1 {t.PRIMARY_LIGHT});
    padding-left: 13px;
}}
QPushButton#navButton:checked:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {t.PRIMARY}58,stop:0.6 {t.VIOLET}42,stop:1 rgba(168,85,247,0.28));
}}

/* Page header */
QLabel#pageTitle {{
    font-size: 26px; font-weight: 800; color: {t.SLATE_900}; letter-spacing: -0.5px;
}}
QLabel#pageSubtitle {{
    font-size: 12.5px; color: {t.SLATE_500}; font-weight: 400; letter-spacing: 0.1px;
}}

/* Banner */
QFrame#topBanner {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #eef2ff,stop:0.35 #e8ecff,stop:0.7 #e0e7ff,stop:1 #dbeafe);
    border: 1.5px solid {t.PRIMARY}12; border-radius: {t.RADIUS_LG}px;
}}
QLabel#bannerTitle {{
    font-size: 19px; font-weight: 800; color: #1e1b4b; letter-spacing: -0.3px;
}}
QLabel#bannerText {{ color: {t.SLATE_600}; font-size: 13px; line-height: 1.5; }}

/* Cards */
QFrame#glassCard {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(255,255,255,0.95),stop:1 rgba(248,250,255,0.90));
    border: 1px solid {t.SLATE_200}B0; border-radius: {t.RADIUS_LG}px;
}}
QFrame#glassCard:hover {{ border: 1px solid {t.PRIMARY}22; }}
QLabel#cardTitle {{
    color: {t.SLATE_500}; font-size: 10px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase;
}}
QLabel#cardValue {{
    color: {t.SLATE_900}; font-size: 32px; font-weight: 800; letter-spacing: -1px;
}}
QLabel#cardSubtitle {{ color: {t.SLATE_400}; font-size: 11px; font-weight: 500; }}

/* Section title */
QLabel#sectionTitle {{
    color: {t.SLATE_900}; font-size: 16px; font-weight: 800; letter-spacing: -0.2px;
}}

/* Panels */
QFrame#panel {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #fcfcff);
    border: 1px solid {t.SLATE_200}A5; border-radius: {t.RADIUS_LG}px;
}}

/* Buttons */
{button_style("primary")}
{button_style("success")}
{button_style("danger")}
{button_style("warning")}
{button_style("info")}
QPushButton#secondaryButton {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 {t.SLATE_50});
    color: {t.SLATE_700}; border: 1.5px solid {t.SLATE_200}; border-radius: {t.RADIUS_MD}px;
    padding: 9px 18px; font-weight: 600; font-size: 13px; min-height: 36px; font-family: {t.FONT_UI};
}}
QPushButton#secondaryButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f5f3ff,stop:1 #ede9fe);
    border-color: #a5b4fc; color: {t.PRIMARY_DARK};
}}
QPushButton#secondaryButton:pressed {{ background: #ede9fe; border-color: {t.PRIMARY_LIGHT}; }}
QPushButton#ghostButton {{
    background: transparent; color: {t.PRIMARY}; border: 1.5px solid {t.PRIMARY}20;
    border-radius: {t.RADIUS_MD}px; padding: 8px 18px; font-size: 13px; font-weight: 600; font-family: {t.FONT_UI};
}}
QPushButton#ghostButton:hover {{ background: {t.PRIMARY}08; border-color: {t.PRIMARY}40; }}

/* Inputs */
{input_style()}

/* Tables */
{table_style()}

/* Tabs */
{tab_style()}

/* Scrollbars */
{scroll_style()}

/* Tooltips */
{tooltip_style()}

/* Labels */
QLabel {{ color: {t.SLATE_700}; }}
QFormLayout QLabel {{ font-size: 12px; font-weight: 700; color: {t.SLATE_600}; padding-top: 3px; letter-spacing: 0.1px; }}

/* GroupBox */
QGroupBox {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #fcfcff);
    border: 1.5px solid {t.SLATE_200}; border-radius: {t.RADIUS_LG}px; margin-top: 12px;
    font-weight: 700; font-size: 13px; color: {t.PRIMARY_DARK}; padding: 18px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 8px; }}

/* List / Tree */
QListWidget, QTreeWidget {{
    background: transparent; border: 1.5px solid {t.SLATE_200}; border-radius: {t.RADIUS_LG}px;
    outline: none; padding: 6px;
}}
QListWidget::item, QTreeWidget::item {{ padding: 8px 12px; border-radius: {t.RADIUS_SM}px; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {t.PRIMARY_LIGHT}18; color: {t.SLATE_900}; }}
QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{ background: {t.SLATE_50}; }}

/* Dialog */
QDialog {{
    background: qlineargradient(x1:0,y1:0,x2:0.5,y2:1,stop:0 {t.SLATE_50},stop:1 {t.SLATE_100});
    border-radius: {t.RADIUS_LG}px;
}}

/* ProgressBar */
QProgressBar {{ border: none; border-radius: {t.RADIUS_SM}px; background: {t.SLATE_100}; text-align: center; color: {t.SLATE_600}; font-weight: 600; }}
QProgressBar::chunk {{ border-radius: {t.RADIUS_SM}px; background: {_grad(t.PRIMARY, t.VIOLET)}; }}

/* Slider */
QSlider::groove:horizontal {{ height: 4px; background: {t.SLATE_200}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {t.PRIMARY}; border-radius: 2px; }}
QSlider::handle:horizontal {{ width: 16px; height: 16px; margin: -6px 0; border-radius: 8px; background: #ffffff; border: 2px solid {t.PRIMARY}; }}
"""


def get_stylesheet() -> str:
    """Return the complete modern application stylesheet."""
    return build_global_stylesheet()


def get_button_style(color: str = "primary", size: str = "medium") -> str:
    """Deprecated — use button_style() directly or global stylesheet."""
    return button_style(color, {"small":"sm","medium":"md","large":"lg"}.get(size, "md"))


def get_card_style(color: str = "white", border_color: str = "rgba(226,232,240,0.65)") -> str:
    """Deprecated — use card_style() directly."""
    return card_style(color, border_color)
