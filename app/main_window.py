from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from PyQt6.QtCore import Qt
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
    QToolButton,
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
    DoctorMedicalReportsPage, DoctorPrescriptionsPage, PatientPrescriptionsPage,
    AIInsightsPage, AdminDashboardPage, AdminAuditLogPage, AdminMedicationsPage,
    AdminPrescriptionsPage, AdminMeasurementsPage,
)
from .presentation.view_models import DoctorReportsViewModel, PrescriptionsViewModel, AIInsightsViewModel
from .ui.modern_styles import get_stylesheet
from .infrastructure.orm.base import SessionLocal

_log = get_logger(__name__)



class MainWindow(QMainWindow):
    def __init__(self, user: User):
        super().__init__()
        self.user = user
        self.selected_patient: User | None = None
        self.setWindowTitle(f"PulseView — {user.full_name} ({user.role_label})")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)
        self.storage = create_storage(user)
        self.data = self.storage.load()
        self.measurements = self.storage.get_measurements()
        self._page_titles: list[tuple[str, str]] = []

        self.setStyleSheet(get_stylesheet())
        self._build_ui()
        self._load_profile()
        self.refresh_all()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(20)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setMinimumWidth(200)
        self.sidebar.setMaximumWidth(300)
        self._sidebar_expanded_width = 260
        self._sidebar_collapsed_width = 70
        self._sidebar_collapsed = False
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(16, 20, 16, 20)
        side_layout.setSpacing(4)
        
        # Collapse/expand button in header
        self._collapse_btn = QToolButton()
        self._collapse_btn.setText("◀")
        self._collapse_btn.setToolTip("Згорнути меню")
        self._collapse_btn.setStyleSheet("""
            QToolButton {
                background: rgba(255,255,255,0.08);
                color: rgba(196,181,253,0.85);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 6px;
                padding: 2px 6px;
                font-size: 11px;
                font-weight: bold;
                min-width: 24px;
                min-height: 24px;
            }
            QToolButton:hover {
                background: rgba(255,255,255,0.15);
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
            }
        """)
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.clicked.connect(self._toggle_sidebar)

        self._brand_layout = QHBoxLayout()
        self._brand_layout.setSpacing(8)
        self._brand_layout.setContentsMargins(0, 0, 0, 0)
        
        # Logo instead of emoji
        self.brand_title = QLabel("PulseView")
        self.brand_title.setObjectName("brandTitle")
        
        self._brand_layout.addWidget(self.brand_title)
        self._brand_layout.addStretch()
        self._brand_layout.addWidget(self._collapse_btn)
        side_layout.addLayout(self._brand_layout)
        
        # Subtitle below logo
        self.brand_subtitle = QLabel(self.user.full_name)
        self.brand_subtitle.setObjectName("brandSubtitle")
        self.brand_subtitle.setWordWrap(True)
        side_layout.addWidget(self.brand_subtitle)
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

        self.logout_btn = QPushButton("← Вийти")
        self.logout_btn.setObjectName("navButton")
        self.logout_btn.setStyleSheet(
            "QPushButton#navButton { color: rgba(252,165,165,0.85); }"
            "QPushButton#navButton:hover { background: rgba(239,68,68,0.12); color: #fca5a5; }"
        )
        self.logout_btn.clicked.connect(self._logout)
        side_layout.addWidget(self.logout_btn)

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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(self.stack)
        content_layout.addWidget(scroll)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content, 1)

        self.stack.currentChanged.connect(self._on_page_changed)

    def _switch_page(self, index: int):
        self._animate_page_transition()
        self.stack.setCurrentIndex(index)
        button = self.nav_group.button(index)
        if button:
            button.setChecked(True)

    def _animate_page_transition(self):
        """Page transition (animations disabled to avoid QPainter conflicts)."""
        pass
    
    def _toggle_sidebar(self):
        """Toggle sidebar between collapsed and expanded states."""
        if self._sidebar_collapsed:
            self._expand_sidebar()
        else:
            self._collapse_sidebar()
    
    def _collapse_sidebar(self):
        """Collapse sidebar to show only icons."""
        self._sidebar_collapsed = True
        self._collapse_btn.setText("▶")
        self._collapse_btn.setToolTip("Розгорнути меню")
        
        # Animate width change
        self._animate_sidebar_width(self._sidebar_collapsed_width)
        
        # Hide subtitle and reduce spacing
        self.brand_subtitle.setVisible(False)
        self.sidebar.setProperty("collapsed", True)
        self.sidebar.style().unpolish(self.sidebar)
        self.sidebar.style().polish(self.sidebar)
        
        # Update layout margins for collapsed state
        self.sidebar.layout().setContentsMargins(8, 16, 8, 16)
        
        # Hide brand title and center the collapse button
        self.brand_title.setVisible(False)
        # Center the collapse button by clearing and rebuilding layout
        # Remove all items from brand layout temporarily
        while self._brand_layout.count():
            item = self._brand_layout.takeAt(0)
            if item.widget() and item.widget() != self._collapse_btn:
                item.widget().setVisible(False)
        # Add stretch on both sides of collapse button to center it
        self._brand_layout.addStretch(1)
        self._brand_layout.addWidget(self._collapse_btn)
        self._brand_layout.addStretch(1)
        
        # Update nav buttons to show only icons
        for btn in self.nav_group.buttons():
            text = btn.text()
            # Extract emoji/icon (first 2 characters for most emojis)
            icon = text[:2] if text else ""
            btn.setProperty("full_text", text)
            btn.setText(icon)
            btn.setToolTip(text)
            # Center the icon with minimal padding
            btn.setStyleSheet(btn.styleSheet() + "QPushButton { text-align: center; padding-left: 4px; padding-right: 4px; }")
        
        # Update logout button
        logout_text = self.logout_btn.text()
        self.logout_btn.setProperty("full_text", logout_text)
        self.logout_btn.setText("←")
        self.logout_btn.setToolTip("← Вийти")
        self.logout_btn.setStyleSheet(
            self.logout_btn.styleSheet() + "QPushButton { text-align: center; padding-left: 4px; padding-right: 4px; }")
    
    def _expand_sidebar(self):
        """Expand sidebar to show full text."""
        self._sidebar_collapsed = False
        self._collapse_btn.setText("◀")
        self._collapse_btn.setToolTip("Згорнути меню")
        
        # Animate width change
        self._animate_sidebar_width(self._sidebar_expanded_width)
        
        # Restore layout margins
        self.sidebar.layout().setContentsMargins(16, 20, 16, 20)
        
        # Show text labels and restore brand layout
        self.brand_title.setVisible(True)
        self.brand_subtitle.setVisible(True)
        
        # Restore original brand layout
        while self._brand_layout.count():
            item = self._brand_layout.takeAt(0)
            if item.widget():
                item.widget().setVisible(True)
        self._brand_layout.addWidget(self.brand_title)
        self._brand_layout.addStretch()
        self._brand_layout.addWidget(self._collapse_btn)
        self.sidebar.setProperty("collapsed", False)
        self.sidebar.style().unpolish(self.sidebar)
        self.sidebar.style().polish(self.sidebar)
        
        # Restore nav button text and left alignment
        for btn in self.nav_group.buttons():
            full_text = btn.property("full_text")
            if full_text:
                btn.setText(full_text)
                btn.setToolTip("")
                # Reset to left alignment (original style)
                btn.setStyleSheet("")
        
        # Restore logout button text and left alignment
        logout_full_text = self.logout_btn.property("full_text")
        if logout_full_text:
            self.logout_btn.setText(logout_full_text)
            self.logout_btn.setToolTip("")
            # Restore original logout button style (left aligned)
            self.logout_btn.setStyleSheet(
                "QPushButton#navButton { color: rgba(252,165,165,0.85); }"
                "QPushButton#navButton:hover { background: rgba(239,68,68,0.12); color: #fca5a5; }")
    
    def _animate_sidebar_width(self, target_width: int):
        """Set sidebar width (animation disabled to avoid sipBadCatcherResult crash)."""
        self.sidebar.setFixedWidth(target_width)

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
        
        # New Prescriptions Page for patient
        db_session = SessionLocal()
        self.patient_prescriptions_vm = PrescriptionsViewModel(self.user, db_session)
        self.patient_prescriptions = PatientPrescriptionsPage(self.patient_prescriptions_vm)
        
        # AI Insights Page for patient
        self.ai_insights_vm = AIInsightsViewModel(self.user, db_session)
        self.ai_insights_page = AIInsightsPage(self.ai_insights_vm)

        return [
            ("📊 Огляд", self.dashboard_page, "Огляд", "Контроль ключових показників"),
            ("📝 Вимірювання", self.measurements_page, "Вимірювання", "Внесення та історія записів"),
            ("📈 Аналітика", self.analytics_page, "Аналітика", "Графіки та порівняння з атм. тиском"),
            ("🤖 AI Інсайти", self.ai_insights_page, "Розумний аналіз", "Прогноз ризику та ДНК-профіль"),
            ("💡 Рекомендації", self.recommendations_page, "Рекомендації лікаря", "Поради від вашого лікаря"),
            ("💊 Мої ліки", self.patient_prescriptions, "Ліки та прийом", "Призначення та календар"),
            ("⚙️ Профіль", self.settings_page, "Профіль", "Особисті дані та експорт JSON"),
        ]

    def _doctor_pages(self):
        self.doctor_detail = DoctorPatientDetailPage(self.storage)
        self.doctor_recommendations = DoctorRecommendationsPage(self.storage)
        self.doctor_thresholds = DoctorThresholdsPage()
        self.doctor_report = DoctorReportPage(self.storage, lambda: self.selected_patient)
        self.doctor_profile = DoctorProfilePage(self.storage)
        
        # New ViewModels and Pages
        db_session = SessionLocal()
        self.doctor_reports_vm = DoctorReportsViewModel(self.user, db_session)
        self.doctor_medical_reports = DoctorMedicalReportsPage(self.doctor_reports_vm)
        
        self.doctor_prescriptions_vm = PrescriptionsViewModel(self.user, db_session)
        self.doctor_prescriptions = DoctorPrescriptionsPage(self.doctor_prescriptions_vm)

        def on_select(patient: User) -> None:
            self.selected_patient = patient
            self.doctor_detail.set_patient(patient)
            self.doctor_medical_reports.set_patient(patient.id, patient.full_name)
            self.doctor_prescriptions.set_patient(patient.id, patient.full_name)
            self._switch_page(1)

        self.doctor_patients = DoctorPatientsPage(self.storage, on_select)

        return [
            ("👥 Пацієнти", self.doctor_patients, "Пацієнти", "Список пацієнтів"),
            ("📋 Дані", self.doctor_detail, "Дані пацієнта", "Вимірювання та графік"),
            ("💡 Рекомендації", self.doctor_recommendations, "Рекомендації", "Поради для пацієнта"),
            ("🎯 Пороги", self.doctor_thresholds, "Пороги пацієнта", "Індивідуальні цільові значення"),
            ("📄 Звіт", self.doctor_report, "Звіт", "Формування HTML-звіту"),
            ("🏥 Мед. звіти", self.doctor_medical_reports, "Медичні звіти", "Професійні медичні звіти"),
            ("💊 Призначення", self.doctor_prescriptions, "Призначення ліків", "Виписка рецептів"),
            ("⚙️ Профіль", self.doctor_profile, "Профіль", "Особисті дані та зміна пароля"),
        ]

    def _admin_pages(self):
        self.admin_dashboard = AdminDashboardPage()
        self.admin_users = AdminUsersPage(self.storage)
        self.admin_audit = AdminAuditLogPage()
        self.admin_medications = AdminMedicationsPage()
        self.admin_prescriptions = AdminPrescriptionsPage()
        self.admin_measurements = AdminMeasurementsPage()
        self.admin_thresholds = AdminThresholdsPage(self.storage)
        return [
            ("📊 Dashboard", self.admin_dashboard, "Статистика", "Системна інформація та метрики"),
            ("👤 Користувачі", self.admin_users, "Користувачі", "Управління обліковими записами"),
            ("📋 Журнал", self.admin_audit, "Журнал аудиту", "Історія всіх дій в системі"),
            ("💊 Ліки", self.admin_medications, "Ліки", "Всі ліки в системі"),
            ("📝 Рецепти", self.admin_prescriptions, "Рецепти", "Всі призначення лікарів"),
            ("📈 Вимірювання", self.admin_measurements, "Вимірювання", "Моніторинг всіх замірів АТ"),
            ("🎯 Пороги", self.admin_thresholds, "Пороги", "Глобальні системні значення"),
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
    from PyQt6.QtCore import QTimer

    def _handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        # Suppress secondary SIP error — the real exception was already logged
        if "sipBadCatcherResult" in str(exc_value):
            return
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _log.error(
            "unhandled_exception",
            exc_type=exc_type.__name__,
            detail=str(exc_value),
            traceback=tb_text,
        )
        # Defer QMessageBox to avoid re-entrant event loop inside SIP virtual callbacks
        QTimer.singleShot(0, lambda: QMessageBox.critical(
            None,
            "Непередбачена помилка",
            f"Сталася непередбачена помилка. Деталі збережено в logs/errors.log.\n\n{exc_value}",
        ))

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
