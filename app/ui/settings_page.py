from __future__ import annotations

from typing import Callable, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..auth import AuthService, User
from ..widgets import SectionTitle


def _make_pass_field(placeholder: str = "") -> tuple[QWidget, QLineEdit]:
    container = QWidget()
    row = QHBoxLayout(container)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(6)
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setEchoMode(QLineEdit.EchoMode.Password)
    toggle = QPushButton("👁")
    toggle.setCheckable(True)
    toggle.setFixedSize(34, 28)
    toggle.setStyleSheet(
        "QPushButton{border:1px solid #d6e2ef;border-radius:8px;background:white;}"
        "QPushButton:checked{background:#e8f3ff;}"
    )
    toggle.toggled.connect(
        lambda on: edit.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
        )
    )
    row.addWidget(edit, 1)
    row.addWidget(toggle)
    return container, edit


class SettingsPage(QWidget):
    def __init__(self, save_profile_callback: Callable, export_callback: Callable, import_callback: Optional[Callable] = None):
        super().__init__()
        self._save_profile_callback = save_profile_callback
        self._export_callback = export_callback
        self._import_callback = import_callback
        self._auth = AuthService()
        self._user: Optional[User] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        layout = QHBoxLayout(inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(inner)
        root.addWidget(scroll)

        # ── Left column: account info + password ──────────────────────────
        left = QVBoxLayout()
        left.setSpacing(18)

        # Account info panel
        info_panel = QFrame()
        info_panel.setObjectName("panel")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(22, 18, 22, 18)
        info_layout.setSpacing(14)
        info_layout.addWidget(SectionTitle("Особисті дані"))

        info_form = QFormLayout()
        info_form.setVerticalSpacing(10)
        info_form.setHorizontalSpacing(16)

        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Прізвище Ім'я По батькові")

        self.username_label = QLabel()
        self.username_label.setStyleSheet("color:#5a7a9a; font-style:italic;")

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@mail.com  (необов'язково)")

        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setSpecialValueText("—")
        self.age_spin.setValue(0)

        self.role_label = QLabel()
        self.role_label.setStyleSheet("color:#5a7a9a; font-style:italic;")

        info_form.addRow("Логін:", self.username_label)
        info_form.addRow("Роль:", self.role_label)
        info_form.addRow("ПІБ:", self.full_name_edit)
        info_form.addRow("Ел. пошта:", self.email_edit)
        info_form.addRow("Вік:", self.age_spin)
        info_layout.addLayout(info_form)

        save_info_btn = QPushButton("💾  Зберегти особисті дані")
        save_info_btn.setObjectName("primaryButton")
        save_info_btn.clicked.connect(self._save_account_info)
        info_layout.addWidget(save_info_btn)
        left.addWidget(info_panel)

        # Password change panel
        pass_panel = QFrame()
        pass_panel.setObjectName("panel")
        pass_layout = QVBoxLayout(pass_panel)
        pass_layout.setContentsMargins(22, 18, 22, 18)
        pass_layout.setSpacing(14)
        pass_layout.addWidget(SectionTitle("Зміна пароля"))

        pass_form = QFormLayout()
        pass_form.setVerticalSpacing(10)
        pass_form.setHorizontalSpacing(16)

        cur_pass_widget, self.cur_pass_edit = _make_pass_field("Поточний пароль")
        new_pass_widget, self.new_pass_edit = _make_pass_field("Мін. 8 символів, велика літера, цифра")
        conf_pass_widget, self.conf_pass_edit = _make_pass_field("Повторіть новий пароль")

        pass_form.addRow("Поточний пароль:", cur_pass_widget)
        pass_form.addRow("Новий пароль:", new_pass_widget)
        pass_form.addRow("Підтвердження:", conf_pass_widget)
        pass_layout.addLayout(pass_form)

        change_pass_btn = QPushButton("🔒  Змінити пароль")
        change_pass_btn.setObjectName("primaryButton")
        change_pass_btn.clicked.connect(self._change_password)
        pass_layout.addWidget(change_pass_btn)
        left.addWidget(pass_panel)
        left.addStretch(1)

        # ── Right column: BP targets + tools ──────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(18)

        targets_panel = QFrame()
        targets_panel.setObjectName("panel")
        targets_layout = QVBoxLayout(targets_panel)
        targets_layout.setContentsMargins(22, 18, 22, 18)
        targets_layout.setSpacing(14)
        targets_layout.addWidget(SectionTitle("Цільові показники АТ"))

        hint = QLabel(
            "Ці значення використовуються для оцінки відхилень "
            "у вимірюваннях та генерації рекомендацій."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#667a90; font-size:12px;")
        targets_layout.addWidget(hint)

        targets_form = QFormLayout()
        targets_form.setVerticalSpacing(10)
        targets_form.setHorizontalSpacing(16)

        self.target_sys_spin = QSpinBox()
        self.target_sys_spin.setRange(80, 180)
        self.target_sys_spin.setSuffix(" мм рт.ст.")

        self.target_dia_spin = QSpinBox()
        self.target_dia_spin.setRange(50, 120)
        self.target_dia_spin.setSuffix(" мм рт.ст.")

        self.target_pulse_spin = QSpinBox()
        self.target_pulse_spin.setRange(40, 150)
        self.target_pulse_spin.setSuffix(" уд/хв")

        targets_form.addRow("Систолічний (верхній):", self.target_sys_spin)
        targets_form.addRow("Діастолічний (нижній):", self.target_dia_spin)
        targets_form.addRow("Пульс:", self.target_pulse_spin)
        targets_layout.addLayout(targets_form)

        save_targets_btn = QPushButton("💾  Зберегти цілі")
        save_targets_btn.setObjectName("primaryButton")
        save_targets_btn.clicked.connect(self._save_targets)
        targets_layout.addWidget(save_targets_btn)
        right.addWidget(targets_panel)

        # Tools panel
        tools_panel = QFrame()
        tools_panel.setObjectName("panel")
        tools_layout = QVBoxLayout(tools_panel)
        tools_layout.setContentsMargins(22, 18, 22, 18)
        tools_layout.setSpacing(12)
        tools_layout.addWidget(SectionTitle("Сервісні дії"))

        tools_desc = QLabel(
            "Усі дані зберігаються в PostgreSQL. Експорт створює резервну копію "
            "вимірювань у форматі JSON."
        )
        tools_desc.setWordWrap(True)
        tools_desc.setStyleSheet("color:#667a90; font-size:12px;")
        tools_layout.addWidget(tools_desc)

        export_btn = QPushButton("📤  Експортувати JSON")
        export_btn.setObjectName("secondaryButton")
        export_btn.clicked.connect(self._export_callback)
        tools_layout.addWidget(export_btn)

        import_btn = QPushButton("📥  Імпортувати JSON")
        import_btn.setObjectName("secondaryButton")
        import_btn.clicked.connect(self._import_json)
        tools_layout.addWidget(import_btn)

        import_hint = QLabel(
            "Імпорт додає вимірювання з файлу в БД. Дублікати (за ID) автоматично пропускаються."
        )
        import_hint.setWordWrap(True)
        import_hint.setStyleSheet("color:#667a90; font-size:11px;")
        tools_layout.addWidget(import_hint)
        right.addWidget(tools_panel)
        right.addStretch(1)

        layout.addLayout(left, 1)
        layout.addLayout(right, 1)

    # ── Public API ────────────────────────────────────────────────────────

    def load_user(self, user: User) -> None:
        """Load all fields from a User object (DB data)."""
        self._user = user
        self.username_label.setText(user.username)
        self.role_label.setText(
            {"patient": "Пацієнт", "doctor": "Лікар", "admin": "Адміністратор"}.get(
                user.role, user.role
            )
        )
        self.full_name_edit.setText(user.full_name)
        self.email_edit.setText(user.email or "")
        self.age_spin.setValue(user.age or 0)
        self.target_sys_spin.setValue(user.target_systolic or 120)
        self.target_dia_spin.setValue(user.target_diastolic or 80)
        self.target_pulse_spin.setValue(user.target_pulse or 75)

    def load_profile(self, profile: dict) -> None:
        """Legacy compatibility — does nothing if load_user was already called."""
        pass

    # ── Private slots ─────────────────────────────────────────────────────

    def _save_account_info(self) -> None:
        if not self._user:
            return
        name = self.full_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "ПІБ не може бути порожнім.")
            return
        email = self.email_edit.text().strip() or None
        age = self.age_spin.value() or None
        try:
            self._auth.update_user(self._user.id, name, self._user.role, age, email)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        # refresh local user object
        self._user = self._auth.get_user(self._user.id)
        QMessageBox.information(self, "Готово", "Особисті дані оновлено.")

    def _save_targets(self) -> None:
        if not self._user:
            return
        sys_v = self.target_sys_spin.value()
        dia_v = self.target_dia_spin.value()
        if dia_v >= sys_v:
            QMessageBox.warning(
                self, "Помилка",
                "Діастолічний тиск повинен бути меншим за систолічний."
            )
            return
        try:
            self._auth.update_user_thresholds(
                self._user.id,
                sys_v,
                dia_v,
                self.target_pulse_spin.value(),
                age=self.age_spin.value() or None,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        # keep legacy callback alive so storage profile is also updated
        self._save_profile_callback({
            "name": self._user.full_name,
            "age": self.age_spin.value() or None,
            "target_systolic": sys_v,
            "target_diastolic": dia_v,
            "target_pulse": self.target_pulse_spin.value(),
        })
        QMessageBox.information(self, "Готово", "Цільові показники збережено.")

    def _import_json(self) -> None:
        if not self._import_callback:
            QMessageBox.information(self, "Імпорт", "Функція імпорту недоступна.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Відкрити JSON для імпорту", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            result = self._import_callback(path)
        except Exception as exc:
            QMessageBox.critical(self, "Помилка імпорту", str(exc))
            return
        imported = result.get("imported", 0)
        errors = result.get("errors", 0)
        msg = f"Імпортовано вимірювань: {imported}"
        if errors:
            msg += f"\nПомилок при імпорті: {errors}"
        QMessageBox.information(self, "Імпорт завершено", msg)

    def _change_password(self) -> None:
        if not self._user:
            return
        cur_pass = self.cur_pass_edit.text()
        new_pass = self.new_pass_edit.text()
        conf_pass = self.conf_pass_edit.text()

        if not cur_pass:
            QMessageBox.warning(self, "Помилка", "Введіть поточний пароль.")
            return
        if not new_pass:
            QMessageBox.warning(self, "Помилка", "Введіть новий пароль.")
            return
        if new_pass != conf_pass:
            QMessageBox.warning(self, "Помилка", "Паролі не збігаються.")
            return

        # Verify current password
        verified = self._auth.login(self._user.username, cur_pass)
        if not verified:
            QMessageBox.warning(self, "Помилка", "Поточний пароль введено невірно.")
            return

        try:
            self._auth.reset_password(self._user.id, new_pass)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return

        self.cur_pass_edit.clear()
        self.new_pass_edit.clear()
        self.conf_pass_edit.clear()
        QMessageBox.information(self, "Готово", "Пароль успішно змінено.")
