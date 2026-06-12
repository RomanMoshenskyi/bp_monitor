from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .auth import AuthService, User


def _password_field(placeholder: str = "") -> tuple[QWidget, QLineEdit]:
    """Поле пароля з кнопкою показу/приховування."""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setEchoMode(QLineEdit.EchoMode.Password)

    toggle = QPushButton("👁")
    toggle.setCheckable(True)
    toggle.setFixedSize(36, 28)
    toggle.setToolTip("Показати пароль")
    toggle.setStyleSheet(
        "QPushButton { border: 1px solid #d6e2ef; border-radius: 8px; background: white; }"
        "QPushButton:checked { background: #e8f3ff; }"
    )

    def on_toggle(checked: bool) -> None:
        edit.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password)
        toggle.setText("🙈" if checked else "👁")

    toggle.toggled.connect(on_toggle)
    layout.addWidget(edit, 1)
    layout.addWidget(toggle)
    return container, edit


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PulseView — вхід")
        self.setFixedSize(440, 500)
        self._auth = AuthService()
        self.user: Optional[User] = None
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Система моніторингу\nартеріального тиску")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1c3150;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._login_tab(), "Вхід")
        tabs.addTab(self._register_tab(), "Реєстрація")
        layout.addWidget(tabs)

        hint = QLabel("Демо: admin/AdminPass123 · doctor/DoctorPass123 · patient/PatientPass123")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #73859d; font-size: 11px;")
        layout.addWidget(hint)

        note = QLabel("Реєстрація доступна лише для пацієнтів. Роль лікаря призначає адміністратор.")
        note.setWordWrap(True)
        note.setStyleSheet("color: #73859d; font-size: 10px;")
        layout.addWidget(note)

    def _login_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Логін")

        login_pass_widget, self.login_password = _password_field()
        form.addRow("Логін:", self.login_username)
        form.addRow("Пароль:", login_pass_widget)

        btn = QPushButton("Увійти")
        btn.setStyleSheet(
            "background: #2f7cf6; color: white; border: none; border-radius: 10px; padding: 10px; font-weight: 700;"
        )
        btn.clicked.connect(self._do_login)
        form.addRow("", btn)
        return w

    def _register_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("Латиниця, без пробілів")
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("example@mail.com")
        self.reg_name = QLineEdit()
        self.reg_name.setPlaceholderText("Прізвище Ім'я По батькові")

        pass_widget, self.reg_password = _password_field("Мін. 8 символів, велика літера, цифра")
        confirm_widget, self.reg_password_confirm = _password_field("Повторіть пароль")

        self.reg_age = QSpinBox()
        self.reg_age.setRange(1, 120)
        self.reg_age.setValue(30)

        form.addRow("Логін:", self.reg_username)
        form.addRow("Ел. пошта:", self.reg_email)
        form.addRow("ПІБ:", self.reg_name)
        form.addRow("Пароль:", pass_widget)
        form.addRow("Підтвердження:", confirm_widget)
        form.addRow("Вік:", self.reg_age)

        btn = QPushButton("Зареєструватися")
        btn.setStyleSheet(
            "background: #2f7cf6; color: white; border: none; border-radius: 10px; padding: 10px; font-weight: 700;"
        )
        btn.clicked.connect(self._do_register)
        form.addRow("", btn)
        return w

    def _do_login(self) -> None:
        user = self._auth.login(self.login_username.text(), self.login_password.text())
        if not user:
            QMessageBox.warning(self, "Помилка", "Невірний логін або пароль.")
            return
        self.user = user
        self.accept()

    def _do_register(self) -> None:
        password = self.reg_password.text()
        confirm = self.reg_password_confirm.text()
        if password != confirm:
            QMessageBox.warning(self, "Помилка", "Паролі не збігаються.")
            return
        try:
            user = self._auth.register(
                self.reg_username.text(),
                password,
                self.reg_name.text(),
                self.reg_email.text(),
                self.reg_age.value(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        QMessageBox.information(
            self,
            "Готово",
            f"Обліковий запис пацієнта створено.\nУвійдіть як {user.username}.",
        )
        self.login_username.setText(user.username)
