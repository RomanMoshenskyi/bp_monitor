from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .auth import ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT, AuthService, User
from .database import close_connection_pool
from .logging_config import get_logger
from .login_window import LoginDialog
from .role_pages import (
    AdminThresholdsPage,
    AdminUsersPage,
    DoctorPatientDetailPage,
    DoctorPatientsPage,
    DoctorProfilePage,
    DoctorRecommendationsPage,
    DoctorReportPage,
    DoctorThresholdsPage,
    PatientRecommendationsView,
)
from .models import Measurement
from .storage import check_database_connection, create_storage
from .ui import (
    AnalyticsPage, DashboardPage, MeasurementsPage, SettingsPage,
)

_log = get_logger(__name__)

APP_STYLE = """
/* ═══════════════════════════════════════════════════════
   PulseView — Premium UI  (Segoe UI Variable / Segoe UI)
   ═══════════════════════════════════════════════════════ */

/* ── Global ──────────────────────────────────────────── */
QMainWindow, QWidget {
    background: #f1f5fb;
    color: #1e293b;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ─────────────────────────────────────────── */
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0.6, y2:1,
        stop:0 #0d1224, stop:0.55 #1a1754, stop:1 #2d267a);
    border-radius: 22px;
}
QFrame#sidebar QWidget, QFrame#sidebar QLabel { background: transparent; }
QLabel#brandTitle {
    color: #ffffff;
    font-size: 21px;
    font-weight: 700;
    letter-spacing: 0.3px;
    background: transparent;
}
QLabel#brandSubtitle {
    color: rgba(196,181,253,0.80);
    font-size: 11.5px;
    background: transparent;
}
QFrame#navDivider {
    background: rgba(255,255,255,0.07);
    max-height: 1px;
    border: none;
}
QLabel#navSectionLabel {
    color: rgba(148,163,184,0.6);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.2px;
    background: transparent;
    padding: 0 4px;
}

/* ── Nav buttons ─────────────────────────────────────── */
QPushButton#navButton {
    text-align: left;
    color: rgba(196,181,253,0.75);
    background: transparent;
    border: none;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton#navButton:hover {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.92);
}
QPushButton#navButton:checked {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(99,102,241,0.50), stop:1 rgba(124,58,237,0.35));
    color: #fff;
    font-weight: 650;
    border-left: 3px solid #818cf8;
    padding-left: 11px;
}
QPushButton#navButton:checked:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 rgba(99,102,241,0.65), stop:1 rgba(124,58,237,0.50));
}

/* ── Page header ─────────────────────────────────────── */
QLabel#pageTitle {
    font-size: 23px;
    font-weight: 700;
    color: #0f172a;
}
QLabel#pageSubtitle {
    font-size: 12px;
    color: #64748b;
}

/* ── Banner ──────────────────────────────────────────── */
QFrame#topBanner {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #eef2ff, stop:1 #dbeafe);
    border: 1px solid rgba(99,102,241,0.14);
    border-radius: 18px;
}
QLabel#bannerTitle { font-size: 18px; font-weight: 700; color: #1e1b4b; }
QLabel#bannerText  { color: #475569; font-size: 13px; }

/* ── Stat cards ──────────────────────────────────────── */
QFrame#glassCard {
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 18px;
}
QLabel#cardTitle {
    color: #64748b;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 0.8px;
}
QLabel#cardValue {
    color: #0f172a;
    font-size: 30px;
    font-weight: 700;
}
QLabel#cardSubtitle { color: #94a3b8; font-size: 11px; }

/* ── Section titles ──────────────────────────────────── */
QLabel#sectionTitle {
    color: #0f172a;
    font-size: 15px;
    font-weight: 700;
}

/* ── Panels ──────────────────────────────────────────── */
QFrame#panel {
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 18px;
}

/* ── Primary button ──────────────────────────────────── */
QPushButton#primaryButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #6366f1, stop:1 #7c3aed);
    color: #fff;
    border: none;
    border-radius: 11px;
    padding: 9px 20px;
    font-weight: 700;
    font-size: 13px;
    min-height: 36px;
}
QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #4f46e5, stop:1 #6d28d9);
}
QPushButton#primaryButton:pressed { background: #4338ca; }
QPushButton#primaryButton:disabled { background: #c7d2fe; color: #e0e7ff; }

/* ── Secondary button ────────────────────────────────── */
QPushButton#secondaryButton {
    background: #fff;
    color: #374151;
    border: 1.5px solid #e2e8f0;
    border-radius: 11px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 34px;
}
QPushButton#secondaryButton:hover {
    background: #f5f3ff;
    border-color: #a5b4fc;
    color: #4f46e5;
}
QPushButton#secondaryButton:pressed { background: #ede9fe; }

/* ── Danger button ───────────────────────────────────── */
QPushButton#dangerButton {
    background: #fff1f2;
    color: #e11d48;
    border: 1.5px solid #fecdd3;
    border-radius: 11px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 34px;
}
QPushButton#dangerButton:hover {
    background: #ffe4e6;
    border-color: #fda4af;
    color: #be123c;
}

/* ── Form labels ─────────────────────────────────────── */
QLabel {
    color: #374151;
}
QFormLayout QLabel {
    font-size: 12.5px;
    font-weight: 600;
    color: #374151;
    padding-top: 2px;
}

/* ── Inputs ──────────────────────────────────────────── */
QLineEdit, QTextEdit, QSpinBox, QComboBox {
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 9px;
    padding: 7px 12px;
    color: #1e293b;
    font-size: 13px;
    min-height: 32px;
    selection-background-color: #c7d2fe;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #6366f1;
    background: #fafaff;
    outline: none;
}
QLineEdit:hover:!focus, QSpinBox:hover:!focus, QComboBox:hover:!focus {
    border-color: #a5b4fc;
}
QLineEdit::placeholder, QTextEdit::placeholder { color: #94a3b8; }
QComboBox {
    padding-right: 30px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1.5px solid #e2e8f0;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    background: #f0f4ff;
}
QComboBox::down-arrow {
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #6366f1;
}
QComboBox::down-arrow:on {
    border-top: none;
    border-bottom: 6px solid #6366f1;
}
QComboBox QAbstractItemView {
    background: white;
    border: 1.5px solid #c7d2fe;
    border-radius: 10px;
    padding: 4px;
    selection-background-color: #eef2ff;
    selection-color: #4f46e5;
    outline: none;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 22px;
    border-radius: 5px;
    background: transparent;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #eef2ff; }

/* ── DateTimeEdit ────────────────────────────────────── */
QDateTimeEdit {
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 9px;
    padding: 7px 12px;
    color: #1e293b;
    font-size: 13px;
    min-height: 32px;
}
QDateTimeEdit:focus   { border-color: #6366f1; background: #fafaff; }
QDateTimeEdit:hover:!focus { border-color: #a5b4fc; }
QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border: none;
    border-left: 1.5px solid #e2e8f0;
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    background: #f0f4ff;
}
QDateTimeEdit::down-arrow {
    width: 0; height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #6366f1;
}

/* ── Table ───────────────────────────────────────────── */
QTableWidget {
    background: white;
    border-radius: 14px;
    border: 1px solid #e8edf5;
    gridline-color: transparent;
    selection-background-color: #eef2ff;
    selection-color: #3730a3;
    outline: none;
    font-size: 13px;
    alternate-background-color: #f8faff;
}
QTableWidget::item {
    padding: 0 12px;
    border: none;
    border-bottom: 1px solid #f1f5f9;
    min-height: 40px;
}
QTableWidget::item:hover  { background: #f0f4ff; }
QTableWidget::item:selected {
    background: #eef2ff;
    color: #3730a3;
    border-left: 3px solid #6366f1;
}
QHeaderView { background: transparent; }
QHeaderView::section {
    background: #f8fafc;
    color: #6366f1;
    padding: 11px 12px;
    border: none;
    border-bottom: 2px solid #e0e7ff;
    font-weight: 700;
    font-size: 11.5px;
    letter-spacing: 0.5px;
}
QHeaderView::section:first { border-top-left-radius: 14px; }
QHeaderView::section:last  { border-top-right-radius: 14px; }

/* ── Tabs ────────────────────────────────────────────── */
QTabWidget::pane {
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    background: white;
    top: -2px;
}
QTabBar::tab {
    background: transparent;
    color: #64748b;
    padding: 9px 22px;
    font-weight: 600;
    font-size: 13px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
}
QTabBar::tab:hover { color: #6366f1; }
QTabBar::tab:selected {
    color: #6366f1;
    border-bottom: 2.5px solid #6366f1;
    font-weight: 700;
}

/* ── Scrollbars ──────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent; width: 7px; margin: 6px 2px;
}
QScrollBar::handle:vertical {
    background: #dde3ed; border-radius: 3px; min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 7px; margin: 2px 6px; }
QScrollBar::handle:horizontal {
    background: #dde3ed; border-radius: 3px; min-width: 28px;
}
QScrollBar::handle:horizontal:hover { background: #94a3b8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Misc ────────────────────────────────────────────── */
QScrollArea  { border: none; background: transparent; }
QCheckBox { spacing: 8px; font-size: 13px; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1.5px solid #c7d2fe;
    border-radius: 5px;
    background: white;
}
QCheckBox::indicator:hover   { border-color: #818cf8; }
QCheckBox::indicator:checked {
    background: #6366f1;
    border-color: #6366f1;
}
QToolTip {
    background: #1e293b; color: white;
    border: none; border-radius: 8px;
    padding: 6px 10px; font-size: 12px;
}
QMessageBox { background: white; }
QMessageBox QPushButton { min-width: 80px; }
"""


class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.selected_patient: User | None = None
        self.setWindowTitle(f"PulseView — {user.full_name} ({user.role_label})")
        self.resize(1440, 880)
        self.setMinimumSize(1100, 700)
        self.storage = create_storage(user)
        self.data = self.storage.load()
        self.measurements = self.storage.get_measurements()
        self._page_titles: list[tuple[str, str]] = []

        self.setStyleSheet(APP_STYLE)
        self._build_ui()
        self._load_profile()
        self.refresh_all()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 28, 16, 20)
        side_layout.setSpacing(4)

        brand = QVBoxLayout()
        brand.setSpacing(2)
        brand_title = QLabel("💓  PulseView")
        brand_title.setObjectName("brandTitle")
        brand_subtitle = QLabel(self.user.full_name)
        brand_subtitle.setObjectName("brandSubtitle")
        brand_subtitle.setWordWrap(True)
        brand.addWidget(brand_title)
        brand.addWidget(brand_subtitle)
        side_layout.addLayout(brand)
        side_layout.addSpacing(16)
        # divider
        div = QFrame()
        div.setObjectName("navDivider")
        div.setFixedHeight(1)
        side_layout.addWidget(div)
        side_layout.addSpacing(8)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.stack = QStackedWidget()

        if self.user.role == ROLE_PATIENT:
            pages = self._patient_pages()
        elif self.user.role == ROLE_DOCTOR:
            pages = self._doctor_pages()
        else:
            pages = self._admin_pages()

        self._page_titles = [("", "")] * len(pages)
        for idx, (name, page, title, subtitle) in enumerate(pages):
            self._page_titles[idx] = (title, subtitle)
            btn = QPushButton(name)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(btn, idx)
            side_layout.addWidget(btn)
            self.stack.addWidget(page)
        self.nav_group.button(0).setChecked(True)

        side_layout.addStretch(1)
        # bottom divider
        div2 = QFrame()
        div2.setObjectName("navDivider")
        div2.setFixedHeight(1)
        side_layout.addWidget(div2)
        side_layout.addSpacing(8)

        logout_btn = QPushButton("→  Вийти")
        logout_btn.setObjectName("navButton")
        logout_btn.setStyleSheet(
            "QPushButton#navButton { color: rgba(252,165,165,0.85); }"
            "QPushButton#navButton:hover { background: rgba(239,68,68,0.12); color: #fca5a5; }"
        )
        logout_btn.clicked.connect(self._logout)
        side_layout.addWidget(logout_btn)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        header = QHBoxLayout()
        header_left = QVBoxLayout()
        self.page_title = QLabel("Огляд")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("Контроль ключових показників і короткий аналітичний висновок")
        self.page_subtitle.setObjectName("pageSubtitle")
        header_left.addWidget(self.page_title)
        header_left.addWidget(self.page_subtitle)

        self.add_quick_btn = QPushButton("+  Додати вимірювання")
        self.add_quick_btn.setObjectName("primaryButton")
        self.add_quick_btn.setFixedHeight(38)
        self.add_quick_btn.clicked.connect(lambda: self._switch_page(1))
        self.add_quick_btn.setVisible(self.user.role == ROLE_PATIENT)

        header.addLayout(header_left)
        header.addStretch(1)
        header.addWidget(self.add_quick_btn)
        content_layout.addLayout(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(self.stack)
        content_layout.addWidget(scroll)

        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)

        self.stack.currentChanged.connect(self._on_page_changed)

    def _switch_page(self, index: int):
        self._animate_page_transition()
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _animate_page_transition(self):
        """Fade the current page out briefly for a smooth feel."""
        widget = self.stack.currentWidget()
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(160)
        anim.setStartValue(0.45)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()

    def _patient_pages(self):
        self.dashboard_page = DashboardPage()
        self.measurements_page = MeasurementsPage(
            add_callback=self.add_measurement,
            delete_callback=self.delete_measurement,
        )
        self.analytics_page = AnalyticsPage()
        self.analytics_page.refresh_handler = self.refresh_all
        self.recommendations_page = PatientRecommendationsView(self.storage)
        self.settings_page = SettingsPage(
            self.save_profile,
            self.export_json,
            import_callback=self.import_json,
        )

        return [
            ("Огляд", self.dashboard_page, "Огляд", "Контроль ключових показників"),
            ("Вимірювання", self.measurements_page, "Вимірювання", "Внесення та історія записів"),
            ("Аналітика", self.analytics_page, "Аналітика", "Графіки та порівняння з атм. тиском"),
            ("Рекомендації", self.recommendations_page, "Рекомендації лікаря", "Поради від вашого лікаря"),
            ("Профіль", self.settings_page, "Профіль", "Особисті дані та експорт JSON"),
        ]

    def _doctor_pages(self):
        self.doctor_detail = DoctorPatientDetailPage(self.storage)
        self.doctor_recommendations = DoctorRecommendationsPage(self.storage)
        self.doctor_thresholds = DoctorThresholdsPage()
        self.doctor_report = DoctorReportPage(self.storage, lambda: self.selected_patient)
        self.doctor_profile = DoctorProfilePage(self.storage)

        def on_select(patient: User) -> None:
            self.selected_patient = patient
            self.doctor_detail.set_patient(patient)
            self._switch_page(1)

        self.doctor_patients = DoctorPatientsPage(self.storage, on_select)

        return [
            ("Пацієнти", self.doctor_patients, "Пацієнти", "Список пацієнтів"),
            ("Дані", self.doctor_detail, "Дані пацієнта", "Вимірювання та графік"),
            ("Рекомендації", self.doctor_recommendations, "Рекомендації", "Поради для пацієнта"),
            ("Пороги", self.doctor_thresholds, "Пороги пацієнта", "Індивідуальні цільові значення"),
            ("Звіт", self.doctor_report, "Звіт", "Формування HTML-звіту"),
            ("Профіль", self.doctor_profile, "Профіль", "Особисті дані та зміна пароля"),
        ]

    def _admin_pages(self):
        self.admin_users = AdminUsersPage(self.storage)
        self.admin_thresholds = AdminThresholdsPage(self.storage)
        return [
            ("Користувачі", self.admin_users, "Користувачі", "Управління обліковими записами"),
            ("Пороги", self.admin_thresholds, "Пороги", "Глобальні системні значення"),
        ]

    def _on_page_changed(self, index: int):
        if 0 <= index < len(self._page_titles):
            title, subtitle = self._page_titles[index]
            self.page_title.setText(title)
            self.page_subtitle.setText(subtitle)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _load_profile(self):
        if self.user.role == ROLE_PATIENT and hasattr(self, "settings_page"):
            fresh = AuthService().get_user(self.user.id)
            if fresh:
                self.settings_page.load_user(fresh)

    def refresh_all(self):
        self.measurements = self.storage.get_measurements()
        self.data = self.storage.load()
        if self.user.role == ROLE_PATIENT:
            if hasattr(self, 'dashboard_page'):
                self.dashboard_page.refresh(self.measurements)
            if hasattr(self, 'measurements_page'):
                self.measurements_page.refresh(self.measurements)
            if hasattr(self, 'analytics_page'):
                self.analytics_page.refresh(self.measurements)
            if hasattr(self, 'recommendations_page'):
                self.recommendations_page.refresh()
            if hasattr(self, 'settings_page'):
                fresh = AuthService().get_user(self.user.id)
                if fresh:
                    self.settings_page.load_user(fresh)
        elif self.user.role == ROLE_DOCTOR:
            self.doctor_patients.refresh()
            if self.selected_patient:
                self.doctor_detail.refresh()
            self.doctor_recommendations.refresh()
            self.doctor_thresholds.refresh()
            if hasattr(self, 'doctor_profile'):
                self.doctor_profile.refresh()
        elif self.user.role == ROLE_ADMIN:
            self.admin_users.refresh()
            self.admin_thresholds.refresh()

    def add_measurement(self, measurement: Measurement):
        self.storage.add_measurement(measurement)
        self.refresh_all()
        QMessageBox.information(self, "Готово", "Нове вимірювання збережено.")

    def delete_measurement(self, measurement_id: str):
        self.storage.delete_measurement(measurement_id)
        self.refresh_all()

    def save_profile(self, profile: dict):
        self.storage.update_profile(profile)
        self.refresh_all()
        QMessageBox.information(self, "Готово", "Профіль користувача оновлено.")

    def _logout(self) -> None:
        _save_session(None)
        self.close()
        login = LoginDialog()
        if login.exec() != login.DialogCode.Accepted or not login.user:
            return
        _save_session(login.user.id)
        window = MainWindow(login.user)
        window.show()
        # Keep reference so Qt doesn't GC it
        self.__class__._reopen_window = window

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Експортувати JSON", "bp_monitor_export.json", "JSON Files (*.json)")
        if not path:
            return
        self.storage.export_to_json(path)
        QMessageBox.information(self, "Експорт", "Файл успішно експортовано.")

    def import_json(self, path: str) -> dict:
        result = self.storage.import_from_json(path)
        self.refresh_all()
        return result


_SESSION_FILE = Path(__file__).resolve().parent.parent / ".session"


def _save_session(user_id) -> None:
    try:
        if user_id is None:
            _SESSION_FILE.unlink(missing_ok=True)
        else:
            _SESSION_FILE.write_text(json.dumps({"user_id": user_id}), encoding="utf-8")
    except Exception:
        pass


def _load_session():
    try:
        if _SESSION_FILE.exists():
            data = json.loads(_SESSION_FILE.read_text(encoding="utf-8"))
            return data.get("user_id")
    except Exception:
        pass
    return None


def _install_global_exception_handler(app) -> None:
    import traceback

    def _handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        _log.exception(
            "unhandled_exception",
            exc_type=exc_type.__name__,
            detail=str(exc_value),
        )
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        QMessageBox.critical(
            None,
            "Непередбачена помилка",
            f"Сталася непередбачена помилка. Деталі збережено в logs/errors.log.\n\n{exc_value}",
        )

    sys.excepthook = _handle


def run_app():
    app = QApplication(sys.argv)
    _install_global_exception_handler(app)
    app.setApplicationName("Система моніторингу кров'яного тиску")
    app.aboutToQuit.connect(close_connection_pool)
    icon_path = Path(__file__).resolve().parent.parent / "assets" / "heart.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    try:
        check_database_connection()
    except Exception as exc:
        QMessageBox.critical(
            None,
            "Помилка підключення до БД",
            "Не вдалося підключитися до PostgreSQL.\n\n"
            f"{exc}\n\n"
            "Перевірте, що сервер PostgreSQL запущений, база bp_monitor створена, "
            "а пароль у config.ini (секція [database]) або змінна DB_PASSWORD правильні.",
        )
        sys.exit(1)

    # Try to restore previous session
    user = None
    saved_id = _load_session()
    if saved_id is not None:
        try:
            user = AuthService().get_user(saved_id)
        except Exception:
            user = None

    if user is None:
        login = LoginDialog()
        if login.exec() != login.DialogCode.Accepted or not login.user:
            sys.exit(0)
        user = login.user
        _save_session(user.id)

    window = MainWindow(user)
    if icon_path.exists():
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    sys.exit(app.exec())
