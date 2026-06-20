"""PulseView — Premium authentication dialog (glassmorphism + micro-interactions)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from .auth import AuthService, User

DS = type("DS", (), {
    "P":"#6366f1","PD":"#4f46e5","PL":"#818cf8","V":"#8b5cf6","VD":"#7c3aed",
    "S":"#10b981","D":"#f43f5e","W":"#f59e0b","A":"#06b6d4","AP":"#ec4899",
    "N1":"#f8fafc","N2":"#f1f5f9","N3":"#e2e8f0","N4":"#cbd5e1",
    "N5":"#94a3b8","N6":"#64748b","N7":"#475569","N8":"#1e293b","N9":"#0f172a",
    "R10":10,"R14":14,"R18":18,"R24":24,
    "S4":4,"S8":8,"S12":12,"S16":16,"S20":20,"S24":24,"S32":32,"S40":40,"S48":48,
    "T12":12,"T13":13,"T14":14,"T16":16,"T20":20,"T26":26,"T32":32,"T40":40,
})()


class AuroraBg(QFrame):
    """Static premium gradient panel (animation disabled to avoid QPainter conflicts)."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,"
            f"stop:0 {DS.P},stop:0.45 {DS.VD},stop:1 {DS.V});"
            f"border-radius:{DS.R18}px;}}"
        )


class GlassBtn(QPushButton):
    """Primary CTA with CSS-based hover state (no QGraphicsEffect to avoid QPainter conflicts)."""
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(48)
        self.setStyleSheet(f"""
            QPushButton{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {DS.P},stop:0.5 {DS.VD},stop:1 {DS.V});color:white;border:none;border-radius:{DS.R14}px;font-size:{DS.T14}px;font-weight:700;padding:0 24px;letter-spacing:0.3px;}}
            QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {DS.PD},stop:0.5 #6d28d9,stop:1 {DS.VD});}}
            QPushButton:pressed{{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4338ca,stop:1 #5b21b6);}}
        """)


class Inp(QFrame):
    """Input wrapper with left icon and error state (no QGraphicsEffect to avoid QPainter conflicts)."""
    def __init__(self, placeholder: str = "", icon: str = "", password: bool = False, parent: QWidget | None = None):
        super().__init__(parent); self._err = False
        row = QHBoxLayout(self); row.setContentsMargins(DS.S12, 0, DS.S12 if not password else DS.S4, 0); row.setSpacing(0)
        self.ico = QLabel(icon); self.ico.setFixedWidth(22); row.addWidget(self.ico)
        self.ed = QLineEdit(); self.ed.setPlaceholderText(placeholder)
        self.ed.setStyleSheet(f"QLineEdit{{background:transparent;border:none;padding:0 4px;font-size:13.5px;color:{DS.N8};min-height:42px;selection-background-color:#c7d2fe;}}")
        if password: self.ed.setEchoMode(QLineEdit.EchoMode.Password)
        row.addWidget(self.ed, 1)
        if password:
            self.eye = QPushButton("***"); self.eye.setCheckable(True); self.eye.setToolTip("Показати / приховати")
            self.eye.setStyleSheet(f"QPushButton{{background:transparent;border:none;color:{DS.N4};font-size:12px;min-width:28px;max-width:28px;min-height:38px;padding:0 2px;}}QPushButton:hover{{color:{DS.P};}}")
            self.eye.toggled.connect(lambda on:(self.ed.setEchoMode(QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password),self.eye.setText("abc" if on else "***")))
            row.addWidget(self.eye)
        self._ss()
        self.ed.textChanged.connect(lambda: self.set_err(False))
    def _ss(self):
        b = DS.D if self._err else DS.N3
        bg = "#fff0f3" if self._err else f"qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafbff,stop:1 #f5f7ff)"
        self.setStyleSheet(f"Inp{{background:{bg};border:1.5px solid {b};border-radius:{DS.R14}px;}}")
        self.ico.setStyleSheet(f"color:{'#f43f5e' if self._err else DS.N4};font-size:14px;background:transparent;")
    def set_err(self, v: bool):
        if self._err == v: return
        self._err = v; self._ss()
    def text(self) -> str: return self.ed.text()
    def setText(self, t: str): self.ed.setText(t)


class Toast(QLabel):
    """Inline self-dismissing notification (no QGraphicsEffect to avoid QPainter conflicts)."""
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent); self.setWordWrap(True); self.setMinimumHeight(36)
        self._visible = False
    def show_msg(self, text: str, kind: str = "error", ms: int = 4000):
        pal = {"error":("#fff0f3","#f43f5e","#fb7185"),"warning":("#fffbeb","#f59e0b","#fbbf24"),"success":("#ecfdf5","#10b981","#34d399"),"info":("#ecfeff","#06b6d4","#22d3ee")}
        bg, fg, bd = pal.get(kind, pal["error"])
        self.setStyleSheet(f"background:{bg};color:{fg};border:1.5px solid {bd}40;border-radius:{DS.R14}px;padding:8px 12px;font-size:12px;font-weight:600;")
        self.setText(text); self._visible = True; self.setVisible(True)
        # Auto-hide disabled to avoid QTimer-related crashes
    def hide_msg(self):
        self._visible = False; self.setVisible(False)


class FadeStack(QStackedWidget):
    """Simple page switcher (QGraphicsOpacityEffect disabled to avoid QPainter conflicts)."""
    def switch(self, idx: int):
        self.setCurrentIndex(idx)


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PulseView — Авторизація")
        self.setMinimumSize(980, 640); self.setMaximumSize(1200, 800); self.resize(1024, 680)
        self.user: Optional[User] = None
        self._auth = AuthService()
        self._build()
        # Entry animation disabled to avoid QGraphicsEffect conflicts
        # self._entry_anim()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter): return
        super().keyPressEvent(e)

    def _build(self):
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        root.addWidget(self._hero(), 55)
        root.addWidget(self._form(), 45)

    # ── Hero ──────────────────────────────────────────────────────
    def _hero(self) -> QFrame:
        fr = QFrame(); fr.setObjectName("heroPanel")
        fr.setStyleSheet(f"QFrame#heroPanel{{background:qlineargradient(x1:0,y1:0,x2:0.6,y2:1,stop:0 #080b1e,stop:0.25 #0f1035,stop:0.55 #1a1260,stop:1 #2a1f7a);}}")
        bg = AuroraBg(fr)
        vl = QVBoxLayout(fr); vl.setContentsMargins(DS.S40, DS.S48, DS.S40, DS.S32); vl.setSpacing(0)

        # Logo + brand
        logo = self._svg("heart.svg", 52)
        if logo:
            l = QLabel(); l.setPixmap(logo); l.setFixedSize(44,44); l.setScaledContents(True); l.setStyleSheet("background:transparent;")
        else:
            l = QLabel(""); l.setStyleSheet("font-size:32px;background:transparent;color:#f43f5e;")
        vl.addWidget(l)
        vl.addSpacing(DS.S8)
        t = QLabel("PulseView"); t.setStyleSheet(f"color:#ffffff;font-size:{DS.T40}px;font-weight:800;letter-spacing:-0.5px;background:transparent;")
        vl.addWidget(t)
        s = QLabel("Система моніторингу артеріального тиску")
        s.setStyleSheet(f"color:rgba(196,181,253,0.75);font-size:{DS.T16}px;background:transparent;font-weight:400;line-height:140%;")
        s.setWordWrap(True); vl.addWidget(s)
        vl.addSpacing(DS.S32)

        # Divider
        d = QFrame(); d.setFixedHeight(1)
        d.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(99,102,241,0.0),stop:0.5 rgba(139,92,246,0.35),stop:1 rgba(99,102,241,0.0));border:none;")
        vl.addWidget(d); vl.addSpacing(DS.S32)

        # Features
        feats = [
            ("Відстеження тиску та пульсу"),
            ("Аналітика та графіки трендів"),
            ("Рекомендації від лікаря"),
            ("Звіти та експорт даних"),
        ]
        fw = QWidget(); fw.setStyleSheet("background:transparent;"); fv = QVBoxLayout(fw); fv.setSpacing(DS.S16); fv.setContentsMargins(0,0,0,0)
        for txt in feats:
            row = QHBoxLayout(); row.setSpacing(DS.S12)
            tx = QLabel(txt); tx.setStyleSheet(f"color:rgba(255,255,255,0.80);font-size:{DS.T14}px;background:transparent;font-weight:500;")
            row.addWidget(tx,1); fv.addLayout(row)
        vl.addWidget(fw); vl.addStretch(1)

        demo = QLabel("Демо-доступ:  admin / AdminPass123")
        demo.setStyleSheet(f"color:rgba(196,181,253,0.40);font-size:{DS.T12}px;background:transparent;font-weight:500;letter-spacing:0.2px;")
        vl.addWidget(demo)

        fr.resizeEvent = lambda e: (bg.setGeometry(0,0,fr.width(),fr.height()), QFrame.resizeEvent(fr,e))
        return fr

    # ── Form ──────────────────────────────────────────────────────
    def _form(self) -> QFrame:
        fr = QFrame(); fr.setObjectName("formPanel")
        fr.setStyleSheet(f"QFrame#formPanel{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff,stop:1 #fafaff);}}")
        # Card shadow via CSS instead of QGraphicsEffect to avoid QPainter conflicts
        fr.setStyleSheet(fr.styleSheet() + "QFrame#formPanel{border-right:1px solid rgba(15,20,60,0.06);}")

        vl = QVBoxLayout(fr); vl.setContentsMargins(DS.S40, DS.S40, DS.S40, DS.S32); vl.setSpacing(0)

        w = QLabel("Ласкаво просимо"); w.setStyleSheet(f"font-size:{DS.T26}px;font-weight:800;color:{DS.N9};letter-spacing:-0.5px;")
        vl.addWidget(w); vl.addSpacing(DS.S4)
        self._sub = QLabel("Увійдіть до свого облікового запису"); self._sub.setStyleSheet(f"font-size:{DS.T14}px;color:{DS.N5};font-weight:400;")
        vl.addWidget(self._sub); vl.addSpacing(DS.S24)

        # Tabs
        self._tabs = QFrame(); self._tabs.setFixedHeight(48); self._tabs.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {DS.N2},stop:1 #eef2ff);border-radius:{DS.R18}px;border:1px solid rgba(226,232,240,0.5);}}")
        tb = QHBoxLayout(self._tabs); tb.setContentsMargins(DS.S4, DS.S4, DS.S4, DS.S4); tb.setSpacing(DS.S4)
        self._tlogin = QPushButton("Вхід"); self._tlogin.setCheckable(True); self._tlogin.setChecked(True); self._tlogin.setCursor(Qt.CursorShape.PointingHandCursor)
        self._treg   = QPushButton("Реєстрація"); self._treg.setCheckable(True); self._treg.setCursor(Qt.CursorShape.PointingHandCursor)
        for b in (self._tlogin, self._treg):
            b.setStyleSheet(f"QPushButton{{background:transparent;color:{DS.N5};border:none;border-radius:{DS.R14}px;font-size:{DS.T14}px;font-weight:600;padding:0 {DS.S16}px;}}QPushButton:checked{{background:#ffffff;color:{DS.P};border:1px solid rgba(99,102,241,0.12);font-weight:700;}}QPushButton:hover:!checked{{color:{DS.P};}}")
            tb.addWidget(b,1)
        self._tlogin.clicked.connect(lambda: self._switch(0)); self._treg.clicked.connect(lambda: self._switch(1))
        vl.addWidget(self._tabs); vl.addSpacing(DS.S24)

        # Toast
        self._toast = Toast(fr); vl.addWidget(self._toast)

        # Stack
        self._stack = FadeStack(); self._stack.addWidget(self._login_pg()); self._stack.addWidget(self._reg_pg())
        vl.addWidget(self._stack, 1)
        return fr

    def _switch(self, idx: int):
        self._stack.switch(idx)
        self._tlogin.setChecked(idx == 0); self._treg.setChecked(idx == 1)
        self._sub.setText("Увійдіть до свого облікового запису" if idx == 0 else "Створіть новий обліковий запис пацієнта")
        self._toast.hide_msg()

    # ── Login page ────────────────────────────────────────────────
    def _login_pg(self) -> QWidget:
        w = QWidget(); w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w); vl.setContentsMargins(0,0,0,0); vl.setSpacing(DS.S16)
        self.inp_login_u = Inp("Введіть логін", "@")
        self.inp_login_p = Inp("Введіть пароль", "*", password=True)
        vl.addWidget(self._row("Логін", self.inp_login_u))
        vl.addWidget(self._row("Пароль", self.inp_login_p))
        vl.addSpacing(DS.S8)
        btn = GlassBtn("Увійти"); btn.clicked.connect(self._do_login); vl.addWidget(btn)
        vl.addStretch(1)
        hint = QLabel("doctor / DoctorPass123  -  patient / PatientPass123")
        hint.setStyleSheet(f"color:{DS.N4};font-size:{DS.T12}px;"); hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(hint)
        return w

    # ── Register page ─────────────────────────────────────────────
    def _reg_pg(self) -> QWidget:
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.Shape.NoFrame)
        sc.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        w = QWidget(); w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w); vl.setContentsMargins(0,0,DS.S8,0); vl.setSpacing(DS.S12)
        self.inp_reg_u = Inp("Латиниця, без пробілів", "@")
        self.inp_reg_e = Inp("example@mail.com", "@")
        self.inp_reg_n = Inp("Прізвище Ім'я По батькові", "U")
        self.inp_reg_p = Inp("Мін. 8 символів", "*", password=True)
        self.inp_reg_pc = Inp("Повторіть пароль", "*", password=True)
        self.inp_reg_a = self._spin(1,120,30)
        for lbl, wg in [("Логін",self.inp_reg_u),("Ел. пошта",self.inp_reg_e),("ПІБ",self.inp_reg_n),
                        ("Пароль",self.inp_reg_p),("Підтвердження пароля",self.inp_reg_pc),("Вік",self.inp_reg_a)]:
            vl.addWidget(self._row(lbl, wg))
        note = QLabel("Самостійна реєстрація — лише для пацієнтів. Роль лікаря призначає адміністратор.")
        note.setWordWrap(True); note.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #fafaff,stop:1 #eef2ff);border:1.5px solid rgba(99,102,241,0.12);border-radius:{DS.R14}px;padding:10px 12px;font-size:12px;color:{DS.N6};font-weight:500;")
        vl.addWidget(note)
        btn = GlassBtn("Створити обліковий запис"); btn.clicked.connect(self._do_register); vl.addWidget(btn)
        vl.addStretch(1)
        sc.setWidget(w); return sc

    def _row(self, label: str, widget: QWidget) -> QWidget:
        c = QWidget(); c.setStyleSheet("background:transparent;")
        v = QVBoxLayout(c); v.setSpacing(DS.S4); v.setContentsMargins(0,0,0,0)
        lbl = QLabel(label); lbl.setStyleSheet(f"font-size:{DS.T12}px;font-weight:700;color:{DS.N7};letter-spacing:0.3px;")
        v.addWidget(lbl); v.addWidget(widget); return c

    def _spin(self, lo, hi, val):
        fr = QFrame(); fr.setStyleSheet(f"QFrame{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #fafbff,stop:1 #f5f7ff);border:1.5px solid {DS.N3};border-radius:{DS.R14}px;}}")
        r = QHBoxLayout(fr); r.setContentsMargins(DS.S12,0,DS.S12,0); r.setSpacing(0)
        sp = QSpinBox(); sp.setRange(lo,hi); sp.setValue(val); sp.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        sp.setStyleSheet(f"QSpinBox{{background:transparent;border:none;padding:0 4px;font-size:13.5px;color:{DS.N8};min-height:42px;}}")
        r.addWidget(sp); fr.spin = sp; return fr

    # ── Entry animation ───────────────────────────────────────────
    def _entry_anim(self):
        # Disabled: QGraphicsOpacityEffect conflicts with QGraphicsDropShadowEffect children
        pass

    # ── Helpers ───────────────────────────────────────────────────
    def _svg(self, name: str, sz: int) -> QPixmap | None:
        p = Path(__file__).resolve().parent.parent / "assets" / name
        if p.exists():
            return QIcon(str(p)).pixmap(sz, sz)
        return None

    # ── Actions ───────────────────────────────────────────────────
    def _do_login(self):
        user = self._auth.login(self.inp_login_u.text(), self.inp_login_p.text())
        if not user:
            self.inp_login_p.set_err(True); self.inp_login_u.set_err(True)
            self._toast.show_msg("Невірний логін або пароль.", "error")
            return
        self.user = user; self.accept()

    def _do_register(self):
        if self.inp_reg_p.text() != self.inp_reg_pc.text():
            self.inp_reg_p.set_err(True); self.inp_reg_pc.set_err(True)
            self._toast.show_msg("Паролі не збігаються.", "error"); return
        try:
            user = self._auth.register(self.inp_reg_u.text(), self.inp_reg_p.text(),
                                       self.inp_reg_n.text(), self.inp_reg_e.text(),
                                       self.inp_reg_a.spin.value())
        except ValueError as exc:
            self._toast.show_msg(str(exc), "error"); return
        self._toast.show_msg(f"Обліковий запис створено. Увійдіть як «{user.username}».", "success", 6000)
        self._switch(0); self.inp_login_u.setText(user.username)
