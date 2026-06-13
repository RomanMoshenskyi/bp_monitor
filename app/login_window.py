from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .auth import AuthService, User

_STYLE = """
QDialog {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0f0c29, stop:0.45 #1e1b4b, stop:1 #302b63);
    font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
}
QFrame#heroPanel { background: transparent; }
QFrame#formPanel { background: #ffffff; border-radius: 0px; }
"""

_FORM_STYLE = """
QFrame#formPanel {
    background: #ffffff;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
}

/* ── Tab switcher pills ─────────────────────────────── */
QFrame#tabBar {
    background: #f1f5f9;
    border-radius: 12px;
}
QPushButton#tabBtn {
    background: transparent;
    color: #64748b;
    border: none;
    border-radius: 10px;
    padding: 8px 0px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton#tabBtn:checked {
    background: #ffffff;
    color: #6366f1;
}
QPushButton#tabBtn:hover:!checked { color: #4f46e5; }

/* ── Input fields ───────────────────────────────────── */
QFrame#inputWrap {
    background: #f8fafc;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
}
QLineEdit#formInput, QSpinBox#formInput {
    background: transparent;
    border: none;
    padding: 0px 4px;
    font-size: 13.5px;
    color: #1e293b;
    min-height: 36px;
    selection-background-color: #c7d2fe;
}
QLineEdit#formInput:focus, QSpinBox#formInput:focus { background: transparent; }

/* ── Primary action button ──────────────────────────── */
QPushButton#actionBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #7c3aed);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 14px;
    font-weight: 700;
    min-height: 46px;
}
QPushButton#actionBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4f46e5, stop:1 #6d28d9);
}
QPushButton#actionBtn:pressed { background: #4338ca; }

/* ── Eye toggle ─────────────────────────────────────── */
QPushButton#eyeBtn {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 16px;
    min-width: 32px; max-width: 32px;
    min-height: 36px;
    padding: 0px 4px;
}
QPushButton#eyeBtn:hover { color: #6366f1; }
QPushButton#eyeBtn:checked { color: #6366f1; }

/* ── Field labels ───────────────────────────────────── */
QLabel#fieldLabel {
    font-size: 12px;
    font-weight: 600;
    color: #475569;
}
"""


def _make_field(placeholder: str = "", password: bool = False) -> tuple[QFrame, QLineEdit]:
    """Returns a styled input wrapper and the inner QLineEdit."""
    wrap = QFrame(); wrap.setObjectName("inputWrap")
    row = QHBoxLayout(wrap)
    row.setContentsMargins(12, 0, 4, 0)
    row.setSpacing(0)
    edit = QLineEdit()
    edit.setObjectName("formInput")
    edit.setPlaceholderText(placeholder)
    if password:
        edit.setEchoMode(QLineEdit.EchoMode.Password)
        eye = QPushButton("👁")
        eye.setObjectName("eyeBtn")
        eye.setCheckable(True)
        eye.setToolTip("Показати / приховати")
        def _toggle(on: bool, e=edit, b=eye):
            e.setEchoMode(QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password)
            b.setText("🙈" if on else "👁")
        eye.toggled.connect(_toggle)
        row.addWidget(edit, 1)
        row.addWidget(eye)
    else:
        row.addWidget(edit, 1)
    return wrap, edit


def _make_spin(lo: int = 1, hi: int = 120, val: int = 30) -> tuple[QFrame, QSpinBox]:
    wrap = QFrame(); wrap.setObjectName("inputWrap")
    row = QHBoxLayout(wrap)
    row.setContentsMargins(12, 0, 12, 0)
    spin = QSpinBox(); spin.setObjectName("formInput")
    spin.setRange(lo, hi); spin.setValue(val)
    spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
    row.addWidget(spin)
    return wrap, spin


def _label(text: str) -> QLabel:
    lbl = QLabel(text); lbl.setObjectName("fieldLabel")
    return lbl


_BTN_STYLE = (
    "QPushButton {"
    "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "    stop:0 #6366f1, stop:1 #7c3aed);"
    "  color: white;"
    "  border: none;"
    "  border-radius: 12px;"
    "  font-size: 14px;"
    "  font-weight: 700;"
    "  min-height: 46px;"
    "  padding: 0 16px;"
    "}"
    "QPushButton:hover {"
    "  background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
    "    stop:0 #4f46e5, stop:1 #6d28d9);"
    "}"
    "QPushButton:pressed { background: #4338ca; }"
)


def _action_btn(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(_BTN_STYLE)
    btn.setDefault(False)
    btn.setAutoDefault(False)
    return btn


def _field_row(label: str, widget: QWidget) -> QVBoxLayout:
    v = QVBoxLayout(); v.setSpacing(5)
    v.addWidget(_label(label))
    v.addWidget(widget)
    return v


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PulseView — Авторизація")
        self.setFixedSize(900, 600)
        self.setStyleSheet(_STYLE)
        self._auth = AuthService()
        self.user: Optional[User] = None
        self._build()

    # ─────────────────────────────────────────────────────────────────────
    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return
        super().keyPressEvent(event)

    def _build(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._hero_panel(), 5)
        root.addWidget(self._form_panel(), 4)

    # ── Hero (left) ───────────────────────────────────────────────────────
    def _hero_panel(self) -> QFrame:
        panel = QFrame(); panel.setObjectName("heroPanel")
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(50, 60, 50, 40)
        vl.setSpacing(0)

        logo = QLabel("💓")
        logo.setStyleSheet("font-size:52px; background:transparent; color:white;")
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft)

        title = QLabel("PulseView")
        title.setStyleSheet(
            "color:#ffffff; font-size:36px; font-weight:800;"
            " background:transparent; letter-spacing:1px;"
        )

        sub = QLabel("Система моніторингу\nартеріального тиску")
        sub.setStyleSheet(
            "color:rgba(196,181,253,0.85); font-size:15px;"
            " background:transparent; line-height:1.5;"
        )

        divider = QFrame(); divider.setFixedHeight(2)
        divider.setStyleSheet("background:rgba(255,255,255,0.1); border:none;")
        divider.setContentsMargins(0, 0, 0, 0)

        features = [
            ("📊", "Відстеження тиску та пульсу"),
            ("📈", "Аналітика та графіки трендів"),
            ("💬", "Рекомендації від лікаря"),
            ("📄", "Звіти та експорт даних"),
        ]
        feat_w = QWidget(); feat_w.setStyleSheet("background:transparent;")
        feat_v = QVBoxLayout(feat_w); feat_v.setSpacing(14); feat_v.setContentsMargins(0, 0, 0, 0)
        for icon, text in features:
            row = QHBoxLayout(); row.setSpacing(12)
            ic = QLabel(icon)
            ic.setStyleSheet(
                "font-size:20px; background:rgba(99,102,241,0.22);"
                " border-radius:10px; padding:4px 8px; color:white;"
            )
            ic.setFixedSize(QSize(40, 40)); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tx = QLabel(text)
            tx.setStyleSheet("color:rgba(255,255,255,0.82); font-size:13px; background:transparent;")
            row.addWidget(ic); row.addWidget(tx); row.addStretch()
            feat_v.addLayout(row)

        demo = QLabel("Демо-доступ: admin / AdminPass123")
        demo.setStyleSheet(
            "color:rgba(196,181,253,0.55); font-size:11px; background:transparent;"
        )
        demo.setAlignment(Qt.AlignmentFlag.AlignLeft)

        vl.addWidget(logo)
        vl.addSpacing(12)
        vl.addWidget(title)
        vl.addSpacing(8)
        vl.addWidget(sub)
        vl.addSpacing(32)
        vl.addWidget(divider)
        vl.addSpacing(28)
        vl.addWidget(feat_w)
        vl.addStretch(1)
        vl.addWidget(demo)
        return panel

    # ── Form (right) ──────────────────────────────────────────────────────
    def _form_panel(self) -> QFrame:
        panel = QFrame(); panel.setObjectName("formPanel")
        panel.setStyleSheet(_FORM_STYLE)
        vl = QVBoxLayout(panel)
        vl.setContentsMargins(44, 44, 44, 36)
        vl.setSpacing(0)

        welcome = QLabel("Ласкаво просимо")
        welcome.setStyleSheet(
            "font-size:24px; font-weight:800; color:#0f172a;"
        )
        vl.addWidget(welcome)
        vl.addSpacing(4)
        self._form_sub = QLabel("Увійдіть до свого облікового запису")
        self._form_sub.setStyleSheet("font-size:13px; color:#64748b;")
        vl.addWidget(self._form_sub)
        vl.addSpacing(24)

        # ── pill tab bar ──
        tab_bar = QFrame(); tab_bar.setObjectName("tabBar")
        tab_bar.setFixedHeight(44)
        tb = QHBoxLayout(tab_bar); tb.setContentsMargins(4, 4, 4, 4); tb.setSpacing(4)
        self._tab_login = QPushButton("🔐  Вхід"); self._tab_login.setObjectName("tabBtn")
        self._tab_login.setCheckable(True); self._tab_login.setChecked(True)
        self._tab_register = QPushButton("📝  Реєстрація"); self._tab_register.setObjectName("tabBtn")
        self._tab_register.setCheckable(True)
        tb.addWidget(self._tab_login, 1); tb.addWidget(self._tab_register, 1)
        self._tab_login.clicked.connect(lambda: self._switch_tab(0))
        self._tab_register.clicked.connect(lambda: self._switch_tab(1))
        vl.addWidget(tab_bar)
        vl.addSpacing(24)

        # ── stacked pages ──
        self._stack = QStackedWidget()
        self._stack.addWidget(self._login_page())
        self._stack.addWidget(self._register_page())
        vl.addWidget(self._stack, 1)

        return panel

    def _switch_tab(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self._tab_login.setChecked(idx == 0)
        self._tab_register.setChecked(idx == 1)
        if idx == 0:
            self._form_sub.setText("Увійдіть до свого облікового запису")
        else:
            self._form_sub.setText("Створіть новий обліковий запис пацієнта")

    # ── Login page ────────────────────────────────────────────────────────
    def _login_page(self) -> QWidget:
        w = QWidget(); w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(16)

        u_wrap, self.login_username = _make_field("Введіть логін")
        p_wrap, self.login_password = _make_field("Введіть пароль", password=True)

        vl.addLayout(_field_row("Логін", u_wrap))
        vl.addLayout(_field_row("Пароль", p_wrap))
        vl.addSpacing(8)

        btn = _action_btn("Увійти  →")
        btn.clicked.connect(self._do_login)
        vl.addWidget(btn)
        vl.addStretch(1)

        hint = QLabel("doctor / DoctorPass123  ·  patient / PatientPass123")
        hint.setStyleSheet("color:#cbd5e1; font-size:10.5px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(hint)
        return w

    # ── Register page ─────────────────────────────────────────────────────
    def _register_page(self) -> QWidget:
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        w = QWidget(); w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w); vl.setContentsMargins(0, 0, 8, 0); vl.setSpacing(12)

        u_wrap, self.reg_username = _make_field("Латиниця, без пробілів")
        e_wrap, self.reg_email    = _make_field("example@mail.com")
        n_wrap, self.reg_name     = _make_field("Прізвище Ім'я По батькові")
        p_wrap, self.reg_password = _make_field("Мін. 8 символів", password=True)
        c_wrap, self.reg_password_confirm = _make_field("Повторіть пароль", password=True)
        a_wrap, self.reg_age      = _make_spin(1, 120, 30)

        for lbl, wgt in [
            ("Логін", u_wrap), ("Ел. пошта", e_wrap), ("ПІБ", n_wrap),
            ("Пароль", p_wrap), ("Підтвердження пароля", c_wrap), ("Вік", a_wrap),
        ]:
            vl.addLayout(_field_row(lbl, wgt))

        note = QLabel("ℹ️  Самостійна реєстрація — лише для пацієнтів. Роль лікаря призначає адміністратор.")
        note.setWordWrap(True)
        note.setStyleSheet(
            "background:#fafaff; border:1px solid #e0e7ff; border-radius:10px;"
            " padding:8px 10px; font-size:11.5px; color:#64748b;"
        )
        vl.addWidget(note)

        btn = _action_btn("Створити обліковий запис  →")
        btn.clicked.connect(self._do_register)
        vl.addWidget(btn)
        vl.addStretch(1)

        scroll.setWidget(w)
        return scroll

    # ── Actions ───────────────────────────────────────────────────────────

    def _do_login(self) -> None:
        user = self._auth.login(self.login_username.text(), self.login_password.text())
        if not user:
            QMessageBox.warning(self, "Помилка входу", "Невірний логін або пароль.")
            return
        self.user = user
        self.accept()

    def _do_register(self) -> None:
        password = self.reg_password.text()
        if password != self.reg_password_confirm.text():
            QMessageBox.warning(self, "Помилка", "Паролі не збігаються.")
            return
        try:
            user = self._auth.register(
                self.reg_username.text(), password,
                self.reg_name.text(), self.reg_email.text(),
                self.reg_age.value(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка реєстрації", str(exc))
            return
        QMessageBox.information(
            self, "Готово",
            f"Обліковий запис створено.\nУвійдіть як «{user.username}».",
        )
        self._switch_tab(0)
        self.login_username.setText(user.username)
