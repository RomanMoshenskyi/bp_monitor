from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .analytics import generate_recommendations, measurement_to_row, summary
from .auth import ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT, AuthService, User
from .reports import build_doctor_report_html, save_doctor_report
from .models import SystemThresholds
from .storage import PostgresStorage
from .widgets import SectionTitle, TrendChart


class DoctorPatientsPage(QWidget):
    def __init__(self, storage: PostgresStorage, on_select: Callable[[User], None]):
        super().__init__()
        self.storage = storage
        self.on_select = on_select
        self._auth = AuthService()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ПІБ", "Вік", "Логін", "Цільовий тиск"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(
            "QTableWidget::item:selected {"
            " background: rgba(47,124,246,0.32);"
            " color: #1c3150;"
            " font-weight: 700;"
            "}"
            "QTableWidget::item:selected:!active {"
            " background: rgba(47,124,246,0.24);"
            " color: #1c3150;"
            "}"
        )
        self.table.doubleClicked.connect(self._open_selected)
        layout.addWidget(self.table)
        btn = QPushButton("Переглянути дані пацієнта")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._open_selected)
        layout.addWidget(btn)

    def refresh(self) -> None:
        patients = self._auth.list_patients()
        self.table.setRowCount(len(patients))
        self._patients = patients
        for i, p in enumerate(patients):
            self.table.setItem(i, 0, QTableWidgetItem(p.full_name))
            self.table.setItem(i, 1, QTableWidgetItem(str(p.age or "—")))
            self.table.setItem(i, 2, QTableWidgetItem(p.username))
            self.table.setItem(
                i, 3, QTableWidgetItem(f"{p.target_systolic}/{p.target_diastolic}")
            )

    def _open_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._patients):
            QMessageBox.information(self, "Увага", "Оберіть пацієнта в таблиці.")
            return
        self.on_select(self._patients[row])


class DoctorPatientDetailPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self.patient: Optional[User] = None
        layout = QVBoxLayout(self)
        self.title = SectionTitle("Дані пацієнта")
        layout.addWidget(self.title)
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("color: #64788e;")
        layout.addWidget(self.stats_label)
        self.chart = TrendChart()
        layout.addWidget(self.chart)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Дата", "Тиск", "Пульс", "Атм.", "Стан", "Ліки", "Активність", "Примітки"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def set_patient(self, patient: User) -> None:
        self.patient = patient
        self.title.setText(f"Пацієнт: {patient.full_name}")
        self.refresh()

    def refresh(self) -> None:
        if not self.patient:
            return
        data = self.storage.get_measurements(self.patient.id)
        stats = summary(data)
        self.stats_label.setText(
            f"Записів: {stats['count']} | Середній тиск: {stats['avg_systolic']}/{stats['avg_diastolic']} | "
            f"Кореляція з атм. тиском: {stats['correlation'] if stats['correlation'] is not None else '—'}"
        )
        last = data[-14:]
        self.chart.set_series(
            [m.systolic for m in last],
            [m.diastolic for m in last],
            [m.timestamp[5:10] for m in last],
            [m.atmospheric_pressure for m in last],
        )
        rows = list(reversed(data))
        self.table.setRowCount(len(rows))
        for ri, m in enumerate(rows):
            for ci, val in enumerate(measurement_to_row(m)):
                self.table.setItem(ri, ci, QTableWidgetItem(val))


class DoctorRecommendationsPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self._auth = AuthService()
        layout = QVBoxLayout(self)
        layout.addWidget(SectionTitle("Рекомендації для пацієнта"))
        self.patient_box = QComboBox()
        self.patient_box.currentIndexChanged.connect(lambda *_: self.refresh())
        layout.addWidget(self.patient_box)
        self.input = QTextEdit()
        self.input.setPlaceholderText("Введіть рекомендацію щодо стану здоров'я...")
        self.input.setMinimumHeight(100)
        layout.addWidget(self.input)
        save_btn = QPushButton("Зберегти рекомендацію")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)
        layout.addWidget(SectionTitle("Історія рекомендацій"))
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history)

    def refresh(self) -> None:
        if self.patient_box.count() == 0:
            self.patient_box.blockSignals(True)
            self.patient_box.clear()
            for patient in self._auth.list_patients():
                self.patient_box.addItem(patient.full_name, patient.id)
            self.patient_box.blockSignals(False)

        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            self.history.clear()
            return
        recs = self.storage.get_doctor_recommendations(patient.id)
        self.history.setPlainText("\n\n".join(f"• {r}" for r in recs) or "Ще немає рекомендацій.")

    def _save(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        text = self.input.toPlainText().strip()
        if not patient:
            QMessageBox.warning(self, "Увага", "Спочатку оберіть пацієнта зі списку.")
            return
        if not text:
            QMessageBox.warning(self, "Увага", "Введіть текст рекомендації.")
            return
        self.storage.add_doctor_recommendation(patient.id, text)
        self.input.clear()
        self.refresh()
        QMessageBox.information(self, "Готово", "Рекомендацію збережено.")


class DoctorThresholdsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._auth = AuthService()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(10)

        self.patient_box = QComboBox()
        self.patient_box.currentIndexChanged.connect(lambda *_: self.refresh())
        panel_layout.addWidget(self.patient_box)

        self.patient_label = QLabel("Оберіть пацієнта зі списку")
        self.patient_label.setStyleSheet("color:#64788e;")
        panel_layout.addWidget(self.patient_label)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.p_sys = QSpinBox()
        self.p_sys.setRange(80, 200)
        self.p_dia = QSpinBox()
        self.p_dia.setRange(50, 130)
        self.p_pulse = QSpinBox()
        self.p_pulse.setRange(40, 150)
        self.p_age = QSpinBox()
        self.p_age.setRange(1, 120)
        form.addRow("Цільовий систолічний:", self.p_sys)
        form.addRow("Цільовий діастолічний:", self.p_dia)
        form.addRow("Цільовий пульс:", self.p_pulse)
        form.addRow("Вік:", self.p_age)
        panel_layout.addLayout(form)

        save_btn = QPushButton("Зберегти для пацієнта")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_patient)
        panel_layout.addWidget(save_btn)

        layout.addWidget(panel)
        layout.addStretch(1)

    def refresh(self) -> None:
        if self.patient_box.count() == 0:
            self.patient_box.blockSignals(True)
            self.patient_box.clear()
            for patient in self._auth.list_patients():
                self.patient_box.addItem(patient.full_name, patient.id)
            self.patient_box.blockSignals(False)

        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            self.patient_label.setText("Оберіть пацієнта зі списку")
            return
    
        self.p_sys.setValue(patient.target_systolic)
        self.p_dia.setValue(patient.target_diastolic)
        self.p_pulse.setValue(patient.target_pulse)
        self.p_age.setValue(patient.age or 30)

    def _save_patient(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            QMessageBox.warning(self, "Увага", "Оберіть пацієнта зі списку.")
            return
        self._auth.update_user_thresholds(
            patient.id,
            self.p_sys.value(),
            self.p_dia.value(),
            self.p_pulse.value(),
            self.p_age.value(),
        )
        updated = self._auth.get_user(patient.id)
        if updated:
            patient.target_systolic = updated.target_systolic
            patient.target_diastolic = updated.target_diastolic
            patient.target_pulse = updated.target_pulse
            patient.age = updated.age
        QMessageBox.information(self, "Готово", "Індивідуальні пороги пацієнта оновлено.")


class DoctorReportPage(QWidget):
    def __init__(self, storage: PostgresStorage, get_patient: Callable[[], Optional[User]]):
        super().__init__()
        self.storage = storage
        self.get_patient = get_patient
        layout = QVBoxLayout(self)
        layout.addWidget(SectionTitle("Звіт для лікаря"))
        desc = QLabel(
            "Формується HTML-звіт з вимірюваннями, рекомендаціями лікаря та автоматичною аналітикою."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        btn = QPushButton("Згенерувати та зберегти звіт")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._generate)
        layout.addWidget(btn)

    def _generate(self) -> None:
        patient = self.get_patient()
        if not patient:
            QMessageBox.warning(self, "Увага", "Оберіть пацієнта.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт", f"report_{patient.username}.html", "HTML (*.html)"
        )
        if not path:
            return
        measurements = self.storage.get_measurements(patient.id)
        doctor_recs = self.storage.get_doctor_recommendations(patient.id)
        auto_recs = generate_recommendations(measurements)
        html = build_doctor_report_html(patient, measurements, doctor_recs, auto_recs)
        save_doctor_report(path, html)
        QMessageBox.information(self, "Готово", f"Звіт збережено:\n{path}")


class _EditUserDialog(QWidget):
    """Floating dialog to edit an existing user."""

    def __init__(self, user: "User", auth: "AuthService", parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle(f"Редагувати: {user.username}")
        self.setFixedWidth(400)
        self._auth = auth
        self._user = user

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setVerticalSpacing(10)

        self.name_edit = QLineEdit(user.full_name)
        self.email_edit = QLineEdit(user.email or "")
        self.email_edit.setPlaceholderText("Необов'язково")
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setSpecialValueText("—")
        self.age_spin.setValue(user.age or 0)
        self.role_box = QComboBox()
        self.role_box.addItem("Пацієнт", ROLE_PATIENT)
        self.role_box.addItem("Лікар", ROLE_DOCTOR)
        self.role_box.addItem("Адміністратор", ROLE_ADMIN)
        self.role_box.setCurrentIndex(
            [ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN].index(user.role)
            if user.role in (ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN) else 0
        )
        self.new_pass_edit = QLineEdit()
        self.new_pass_edit.setPlaceholderText("Залиште порожнім — без змін")
        self.new_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)

        layout.addRow("ПІБ:", self.name_edit)
        layout.addRow("Ел. пошта:", self.email_edit)
        layout.addRow("Вік:", self.age_spin)
        layout.addRow("Роль:", self.role_box)
        layout.addRow("Новий пароль:", self.new_pass_edit)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addRow("", btn_row)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "ПІБ не може бути порожнім.")
            return
        age = self.age_spin.value() or None
        email = self.email_edit.text().strip() or None
        role = self.role_box.currentData()
        new_pass = self.new_pass_edit.text()
        try:
            self._auth.update_user(self._user.id, name, role, age, email)
            if new_pass:
                self._auth.reset_password(self._user.id, new_pass)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        QMessageBox.information(self, "Готово", "Дані користувача оновлено.")
        self.close()
        if self.parent() and hasattr(self.parent(), "refresh"):
            self.parent().refresh()


class AdminUsersPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self._auth = AuthService()
        self._users: List[User] = []
        layout = QVBoxLayout(self)
        layout.addWidget(SectionTitle("Користувачі"))

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ПІБ", "Логін", "Ел. пошта", "Роль", "Вік", "Статус", "Дії"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet(
            "QTableWidget::item:selected {"
            " background: rgba(47,124,246,0.32);"
            " color: #1c3150;"
            " font-weight: 700;"
            "}"
            "QTableWidget::item:selected:!active {"
            " background: rgba(47,124,246,0.24);"
            " color: #1c3150;"
            "}"
        )
        layout.addWidget(self.table)

        # Action buttons row
        btn_row = QHBoxLayout()
        edit_btn = QPushButton("✏️  Редагувати вибраного")
        edit_btn.setObjectName("secondaryButton")
        edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(edit_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        form_frame = QFrame()
        form_frame.setObjectName("panel")
        form = QFormLayout(form_frame)
        form.setVerticalSpacing(8)
        self.new_login = QLineEdit()
        self.new_login.setPlaceholderText("Обов'язково")
        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("Мін. 8 символів, велика літера, цифра")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("Обов'язково")
        self.new_email = QLineEdit()
        self.new_email.setPlaceholderText("Необов'язково")
        self.new_age = QSpinBox()
        self.new_age.setRange(0, 120)
        self.new_age.setSpecialValueText("—")
        self.new_age.setValue(0)
        self.new_role = QComboBox()
        self.new_role.addItem("Пацієнт", ROLE_PATIENT)
        self.new_role.addItem("Лікар", ROLE_DOCTOR)
        self.new_role.addItem("Адміністратор", ROLE_ADMIN)
        form.addRow("Логін:", self.new_login)
        form.addRow("Пароль:", self.new_pass)
        form.addRow("ПІБ:", self.new_name)
        form.addRow("Ел. пошта:", self.new_email)
        form.addRow("Вік:", self.new_age)
        form.addRow("Роль:", self.new_role)
        add_btn = QPushButton("Додати користувача")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_user)
        form.addRow("", add_btn)
        layout.addWidget(form_frame)

    def refresh(self) -> None:
        users = self._auth.list_users()
        self._users = users
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.table.setItem(i, 0, QTableWidgetItem(u.full_name))
            self.table.setItem(i, 1, QTableWidgetItem(u.username))
            self.table.setItem(i, 2, QTableWidgetItem(u.email or "—"))
            self.table.setItem(i, 3, QTableWidgetItem(u.role_label))
            self.table.setItem(i, 4, QTableWidgetItem(str(u.age) if u.age else "—"))
            self.table.setItem(i, 5, QTableWidgetItem("Активний" if u.is_active else "Заблокований"))
            btn = QPushButton("Деактивувати" if u.is_active else "Активувати")
            btn.clicked.connect(lambda _, uid=u.id, active=u.is_active: self._toggle(uid, active))
            self.table.setCellWidget(i, 6, btn)

    def _toggle(self, user_id: int, is_active: bool) -> None:
        self._auth.set_user_active(user_id, not is_active)
        self.refresh()

    def _edit_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._users):
            QMessageBox.information(self, "Увага", "Оберіть користувача в таблиці.")
            return
        dlg = _EditUserDialog(self._users[row], self._auth, parent=self)
        dlg.show()

    def _add_user(self) -> None:
        login = self.new_login.text().strip()
        password = self.new_pass.text()
        name = self.new_name.text().strip()
        email = self.new_email.text().strip() or None
        age = self.new_age.value() or None
        role = self.new_role.currentData()

        if not login:
            QMessageBox.warning(self, "Помилка", "Введіть логін.")
            return
        if not password:
            QMessageBox.warning(self, "Помилка", "Введіть пароль.")
            return
        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть ПІБ.")
            return

        try:
            self._auth.create_user(login, password, name, role, age=age, email=email)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        self.new_login.clear()
        self.new_pass.clear()
        self.new_name.clear()
        self.new_email.clear()
        self.new_age.setValue(0)
        self.refresh()
        QMessageBox.information(self, "Готово", f"Користувача «{login}» додано.")


class AdminThresholdsPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        hint = QLabel("Глобальні системні значення")
        hint.setStyleSheet("color:#73859d; font-size:12px;")
        layout.addWidget(hint)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(10)

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        self.sys_high = QSpinBox()
        self.sys_high.setRange(100, 220)
        self.dia_high = QSpinBox()
        self.dia_high.setRange(60, 150)
        self.sys_low = QSpinBox()
        self.sys_low.setRange(60, 150)
        self.dia_low = QSpinBox()
        self.dia_low.setRange(40, 100)
        self.pulse_high = QSpinBox()
        self.pulse_high.setRange(60, 200)
        self.pulse_low = QSpinBox()
        self.pulse_low.setRange(30, 100)
        form.addRow("Систолічний (верх):", self.sys_high)
        form.addRow("Діастолічний (верх):", self.dia_high)
        form.addRow("Систолічний (низ):", self.sys_low)
        form.addRow("Діастолічний (низ):", self.dia_low)
        form.addRow("Пульс (верх):", self.pulse_high)
        form.addRow("Пульс (низ):", self.pulse_low)
        panel_layout.addLayout(form)

        save_btn = QPushButton("Зберегти пороги")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_global)
        panel_layout.addWidget(save_btn)

        layout.addWidget(panel)
        layout.addStretch(1)

    def refresh(self) -> None:
        t = self.storage.get_system_thresholds()
        self.sys_high.setValue(t.systolic_high)
        self.dia_high.setValue(t.diastolic_high)
        self.sys_low.setValue(t.systolic_low)
        self.dia_low.setValue(t.diastolic_low)
        self.pulse_high.setValue(t.pulse_high)
        self.pulse_low.setValue(t.pulse_low)

    def _save_global(self) -> None:
        self.storage.update_system_thresholds(
            SystemThresholds(
                self.sys_high.value(),
                self.dia_high.value(),
                self.sys_low.value(),
                self.dia_low.value(),
                self.pulse_high.value(),
                self.pulse_low.value(),
            )
        )
        QMessageBox.information(self, "Готово", "Глобальні пороги збережено.")


class PatientRecommendationsView(QWidget):
    """Перегляд рекомендацій лікаря для пацієнта."""

    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        layout = QVBoxLayout(self)
        layout.addWidget(SectionTitle("Рекомендації лікаря"))
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

    def refresh(self) -> None:
        recs = self.storage.get_doctor_recommendations(self.storage.user.id)
        self.text.setPlainText("\n\n".join(f"• {r}" for r in recs) or "Поки немає рекомендацій від лікаря.")
