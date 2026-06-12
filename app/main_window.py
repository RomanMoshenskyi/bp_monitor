from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
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
QMainWindow, QWidget {
    background: #edf4fb;
    color: #20334b;
    font-family: 'Segoe UI';
    font-size: 13px;
}
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #173456, stop:1 #1e4b7a);
    border-radius: 24px;
}
QFrame#sidebar QWidget,
QFrame#sidebar QLabel {
    background: transparent;
}
QLabel#brandTitle {
    color: white;
    font-size: 24px;
    font-weight: 700;
    background: transparent;
}
QLabel#brandSubtitle {
    color: rgba(255,255,255,0.85);
    font-size: 13px;
    background: transparent;
}
QPushButton#navButton {
    text-align: left;
    color: rgba(255,255,255,0.88);
    background: transparent;
    border: none;
    padding: 12px 16px;
    border-radius: 14px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#navButton:hover {
    background: rgba(255,255,255,0.09);
}
QPushButton#navButton:checked {
    background: rgba(255,255,255,0.16);
    color: white;
}
QLabel#pageTitle {
    font-size: 26px;
    font-weight: 700;
    color: #1c2f49;
}
QLabel#pageSubtitle {
    font-size: 13px;
    color: #73859d;
}
QFrame#topBanner {
    background: #edf4fb;
    border: none;
    border-radius: 0;
}
QLabel#bannerTitle {
    font-size: 20px;
    font-weight: 700;
    color: #1c3150;
}
QLabel#bannerText {
    color: #60748a;
    font-size: 13px;
}
QFrame#glassCard {
    background: rgba(255,255,255,0.98);
    border: 1px solid rgba(209,225,240,0.9);
    border-radius: 20px;
}
QLabel#cardTitle {
    color: #74859b;
    font-size: 12px;
    font-weight: 600;
}
QLabel#cardValue {
    color: #1d3250;
    font-size: 30px;
    font-weight: 700;
}
QLabel#cardSubtitle {
    color: #70839a;
    font-size: 12px;
}
QLabel#sectionTitle {
    color: #1c3150;
    font-size: 18px;
    font-weight: 700;
}
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #2f7cf6, stop:1 #40a9ff);
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 18px;
    font-weight: 700;
}
QPushButton#primaryButton:hover {
    background: #266ee0;
}
QPushButton#secondaryButton {
    background: white;
    color: #28435f;
    border: 1px solid #d6e2ef;
    border-radius: 14px;
    padding: 11px 16px;
    font-weight: 700;
}
QPushButton#secondaryButton:hover {
    background: #f7fbff;
}
QFrame#panel {
    background: rgba(255,255,255,0.98);
    border: 1px solid rgba(209,225,240,0.95);
    border-radius: 20px;
}
QLineEdit, QTextEdit, QSpinBox, QComboBox, QDateTimeEdit {
    background: white;
    border: 1px solid #d6e2ef;
    border-radius: 12px;
    padding: 8px 10px;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {
    border: 1px solid #2f7cf6;
}
QTableWidget {
    background: white;
    border-radius: 16px;
    border: 1px solid #d9e5f2;
    gridline-color: #eef4fa;
    selection-background-color: #dbeafe;
    selection-color: #1c3150;
}
QHeaderView::section {
    background: #f5f9fd;
    color: #60748a;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #e5eef6;
    font-weight: 700;
}
QScrollArea {
    border: none;
}
QCheckBox {
    spacing: 8px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.selected_patient: User | None = None
        self.setWindowTitle(f"PulseView — {user.full_name} ({user.role_label})")
        self.resize(1450, 900)
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
        sidebar.setFixedWidth(280)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(18, 24, 18, 24)
        side_layout.setSpacing(12)

        brand = QVBoxLayout()
        brand_title = QLabel("PulseView")
        brand_title.setObjectName("brandTitle")
        brand_subtitle = QLabel(self.user.full_name)
        brand_subtitle.setObjectName("brandSubtitle")
        brand_subtitle.setWordWrap(True)
        brand.addWidget(brand_title)
        brand.addWidget(brand_subtitle)
        side_layout.addLayout(brand)
        side_layout.addSpacing(10)

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

        logout_btn = QPushButton("Вийти")
        logout_btn.setObjectName("navButton")
        logout_btn.clicked.connect(self._logout)
        side_layout.addWidget(logout_btn)

        side_layout.addStretch(1)

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

        self.add_quick_btn = QPushButton("Швидко додати запис")
        self.add_quick_btn.setObjectName("primaryButton")
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
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _patient_pages(self):
        self.dashboard_page = DashboardPage()
        self.measurements_page = MeasurementsPage(
            add_callback=self.add_measurement,
            delete_callback=self.delete_measurement,
        )
        self.analytics_page = AnalyticsPage()
        self.analytics_page.refresh_handler = self.refresh_all
        self.settings_page = SettingsPage(
            self.save_profile,
            self.export_json,
            import_callback=self.import_json,
        )

        return [
            ("Огляд", self.dashboard_page, "Огляд", "Контроль ключових показників"),
            ("Вимірювання", self.measurements_page, "Вимірювання", "Внесення та історія записів"),
            ("Аналітика", self.analytics_page, "Аналітика", "Графіки та порівняння з атм. тиском"),
            ("Профіль", self.settings_page, "Профіль", "Особисті дані та експорт JSON"),
        ]

    def _doctor_pages(self):
        self.doctor_detail = DoctorPatientDetailPage(self.storage)
        self.doctor_recommendations = DoctorRecommendationsPage(self.storage)
        self.doctor_thresholds = DoctorThresholdsPage()
        self.doctor_report = DoctorReportPage(self.storage, lambda: self.selected_patient)

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
