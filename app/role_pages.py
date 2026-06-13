from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
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
from .widgets import GlassCard, SectionTitle, TrendChart


# ─── helpers ──────────────────────────────────────────────────────────────────

def _panel(title: str = "", spacing: int = 14) -> tuple[QFrame, QVBoxLayout]:
    f = QFrame(); f.setObjectName("panel")
    v = QVBoxLayout(f)
    v.setContentsMargins(22, 18, 22, 18)
    v.setSpacing(spacing)
    if title:
        v.addWidget(SectionTitle(title))
    return f, v


def _styled_table(cols: int, headers: list[str]) -> QTableWidget:
    t = QTableWidget(0, cols)
    t.setHorizontalHeaderLabels(headers)
    t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    t.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    t.verticalHeader().setVisible(False)
    t.setAlternatingRowColors(True)
    t.setShowGrid(False)
    t.verticalHeader().setDefaultSectionSize(42)
    return t


def _role_badge(role: str) -> QLabel:
    _MAP = {
        ROLE_PATIENT: ("#d1fae5", "#059669", "Пацієнт"),
        ROLE_DOCTOR:  ("#dbeafe", "#1d4ed8", "Лікар"),
        ROLE_ADMIN:   ("#fce7f3", "#9d174d", "Адміністратор"),
    }
    bg, fg, text = _MAP.get(role, ("#f3f4f6", "#6b7280", role))
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setStyleSheet(
        f"background:{bg}; color:{fg}; border-radius:10px;"
        f"padding:3px 10px; font-size:11px; font-weight:700;"
    )
    return lbl


# ─── Doctor pages ──────────────────────────────────────────────────────────────

class DoctorPatientsPage(QWidget):
    def __init__(self, storage: PostgresStorage, on_select: Callable[[User], None]):
        super().__init__()
        self.storage = storage
        self.on_select = on_select
        self._auth = AuthService()
        self._patients: List[User] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # banner
        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("👥  Список пацієнтів"); t.setObjectName("bannerTitle")
        s = QLabel("Оберіть пацієнта для перегляду вимірювань, аналітики та рекомендацій")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s)
        bl.addLayout(bt, 1)
        layout.addWidget(banner)

        panel, vl = _panel()
        # search + refresh row
        top_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Пошук за ім'ям або логіном…")
        self._search.textChanged.connect(self._filter)
        refresh_btn = QPushButton("↻  Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(110)
        refresh_btn.clicked.connect(self.refresh)
        top_row.addWidget(self._search, 1)
        top_row.addWidget(refresh_btn)
        vl.addLayout(top_row)

        self.table = _styled_table(5, ["👤 ПІБ", "🎂 Вік", "🔑 Логін", "🎯 Цільовий тиск", "📊 Записів"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(self._open_selected)
        vl.addWidget(self.table)

        btn_row = QHBoxLayout()
        open_btn = QPushButton("📋  Переглянути дані пацієнта")
        open_btn.setObjectName("primaryButton")
        open_btn.clicked.connect(self._open_selected)
        btn_row.addStretch(1); btn_row.addWidget(open_btn)
        vl.addLayout(btn_row)
        layout.addWidget(panel)

    def refresh(self) -> None:
        self._patients = self._auth.list_patients()
        self._render(self._patients)

    def _render(self, patients: List[User]) -> None:
        self.table.setRowCount(len(patients))
        for i, p in enumerate(patients):
            count = len(self.storage.get_measurements(p.id))
            vals = [p.full_name, str(p.age or "—"), p.username,
                    f"{p.target_systolic}/{p.target_diastolic}", str(count)]
            row_bg = QColor("#f8faff") if i % 2 else QColor("#ffffff")
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c > 0
                                      else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setBackground(row_bg)
                self.table.setItem(i, c, item)

    def _filter(self, text: str) -> None:
        q = text.lower()
        filtered = [p for p in self._patients
                    if q in p.full_name.lower() or q in p.username.lower()] if q else self._patients
        self._render(filtered)
        self._filtered = filtered

    def _open_selected(self) -> None:
        row = self.table.currentRow()
        src = getattr(self, "_filtered", self._patients)
        if row < 0 or row >= len(src):
            QMessageBox.information(self, "Увага", "Оберіть пацієнта в таблиці.")
            return
        self.on_select(src[row])


class DoctorPatientDetailPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self.patient: Optional[User] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # patient info banner
        self.banner = QFrame(); self.banner.setObjectName("topBanner")
        bl = QHBoxLayout(self.banner); bl.setContentsMargins(24, 18, 24, 18); bl.setSpacing(24)
        info_col = QVBoxLayout(); info_col.setSpacing(4)
        self.patient_title = QLabel("Оберіть пацієнта"); self.patient_title.setObjectName("bannerTitle")
        self.patient_subtitle = QLabel(""); self.patient_subtitle.setObjectName("bannerText")
        self.patient_subtitle.setWordWrap(True)
        info_col.addWidget(self.patient_title); info_col.addWidget(self.patient_subtitle)
        bl.addLayout(info_col, 1)
        layout.addWidget(self.banner)

        # stat cards row
        self.cards_row = QHBoxLayout(); self.cards_row.setSpacing(14)
        self._stat_cards = [
            GlassCard("📋 Записів", "—", "", accent_index=0),
            GlassCard("🩺 Серед. тиск", "—", "мм рт. ст.", accent_index=3),
            GlassCard("💓 Серед. пульс", "—", "уд/хв", accent_index=1),
            GlassCard("📈 Кореляція", "—", "з атм. тиском", accent_index=2),
        ]
        for c in self._stat_cards: self.cards_row.addWidget(c)
        layout.addLayout(self.cards_row)

        # chart + table
        center = QHBoxLayout(); center.setSpacing(16)
        chart_panel, cvl = _panel("📈  Тренд (останні 14 вимірювань)")
        self.chart = TrendChart()
        cvl.addWidget(self.chart)
        center.addWidget(chart_panel, 3)
        layout.addLayout(center)

        tbl_panel, tvl = _panel("📋  Всі вимірювання")
        self.table = _styled_table(8,
            ["📅 Дата", "🩺 Тиск", "💓 Пульс", "🌡 Атм.", "😌 Стан", "💊 Ліки", "🏃 Активність", "📝 Примітки"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        hdr.setDefaultSectionSize(110)
        tvl.addWidget(self.table)
        layout.addWidget(tbl_panel)

    def set_patient(self, patient: User) -> None:
        self.patient = patient
        self.patient_title.setText(f"👤  {patient.full_name}")
        self.patient_subtitle.setText(
            f"Логін: {patient.username}  ·  Вік: {patient.age or '—'}  ·  "
            f"Цільовий тиск: {patient.target_systolic}/{patient.target_diastolic}"
        )
        self.refresh()

    def refresh(self) -> None:
        if not self.patient:
            return
        data = self.storage.get_measurements(self.patient.id)
        stats = summary(data)
        self._stat_cards[0].update_content("📋 Записів", str(stats["count"]), "")
        self._stat_cards[1].update_content("🩺 Серед. тиск",
            f"{stats['avg_systolic']}/{stats['avg_diastolic']}", "мм рт. ст.")
        avg_p = round(sum(m.pulse for m in data) / max(len(data), 1))
        self._stat_cards[2].update_content("💓 Серед. пульс", str(avg_p), "уд/хв")
        corr = stats["correlation"]
        self._stat_cards[3].update_content("📈 Кореляція",
            str(corr) if corr is not None else "—", "з атм. тиском")

        last = data[-14:]
        self.chart.set_series([m.systolic for m in last], [m.diastolic for m in last],
                               [m.timestamp[5:10] for m in last],
                               [m.atmospheric_pressure for m in last])
        rows = list(reversed(data))
        self.table.setRowCount(len(rows))
        for ri, m in enumerate(rows):
            row_bg = QColor("#f8faff") if ri % 2 else QColor("#ffffff")
            for ci, val in enumerate(measurement_to_row(m)):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if ci < 7
                                      else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setBackground(row_bg)
                if ci == 1:
                    try:
                        sv = int(val.split("/")[0])
                        if sv >= 140: item.setForeground(QColor("#e11d48")); f=QFont(); f.setBold(True); item.setFont(f)
                        elif sv < 100: item.setForeground(QColor("#d97706"))
                        else: item.setForeground(QColor("#16a34a"))
                    except Exception: pass
                self.table.setItem(ri, ci, item)


class DoctorRecommendationsPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self._auth = AuthService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("💬  Рекомендації для пацієнта"); t.setObjectName("bannerTitle")
        s = QLabel("Записуйте індивідуальні поради. Пацієнт бачить їх у своєму профілі.")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        layout.addWidget(banner)

        main_row = QHBoxLayout(); main_row.setSpacing(16)

        # left: write panel
        write_panel, wl = _panel("✍️  Нова рекомендація")
        sel_row = QHBoxLayout()
        sel_lbl = QLabel("Пацієнт:"); sel_lbl.setStyleSheet("font-weight:600; color:#374151;")
        self.patient_box = QComboBox()
        self.patient_box.currentIndexChanged.connect(lambda *_: self._load_history())
        sel_row.addWidget(sel_lbl); sel_row.addWidget(self.patient_box, 1)
        wl.addLayout(sel_row)
        self.input = QTextEdit()
        self.input.setPlaceholderText("Введіть рекомендацію…\n\nНаприклад: знизити вживання солі, збільшити фізичну активність.")
        self.input.setMinimumHeight(120)
        self.input.setStyleSheet(
            "QTextEdit{background:#fafaff;border:1.5px solid #e0e7ff;border-radius:10px;padding:10px;font-size:13px;}"
        )
        wl.addWidget(self.input)
        save_btn = QPushButton("💾  Зберегти рекомендацію")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        wl.addWidget(save_btn)
        main_row.addWidget(write_panel, 1)

        # right: history
        hist_panel, hl = _panel("📜  Історія рекомендацій")
        self.history = QTextEdit(); self.history.setReadOnly(True)
        self.history.setStyleSheet(
            "QTextEdit{background:#fafaff;border:1.5px solid #e0e7ff;border-radius:10px;padding:10px;font-size:13px;}"
        )
        hl.addWidget(self.history)
        main_row.addWidget(hist_panel, 1)

        layout.addLayout(main_row)

    def refresh(self) -> None:
        self.patient_box.blockSignals(True)
        self.patient_box.clear()
        for p in self._auth.list_patients():
            self.patient_box.addItem(p.full_name, p.id)
        self.patient_box.blockSignals(False)
        self._load_history()

    def _load_history(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            self.history.clear(); return
        recs = self.storage.get_doctor_recommendations(patient.id)
        self.history.setPlainText("\n\n".join(f"• {r}" for r in recs) or "Ще немає рекомендацій.")

    def _save(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        text = self.input.toPlainText().strip()
        if not patient:
            QMessageBox.warning(self, "Увага", "Оберіть пацієнта."); return
        if not text:
            QMessageBox.warning(self, "Увага", "Введіть текст."); return
        self.storage.add_doctor_recommendation(patient.id, text)
        self.input.clear()
        self._load_history()
        QMessageBox.information(self, "Готово", "Рекомендацію збережено.")


class DoctorThresholdsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._auth = AuthService()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("🎯  Індивідуальні цільові значення"); t.setObjectName("bannerTitle")
        s = QLabel("Встановіть персональні пороги тиску та пульсу для кожного пацієнта.")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        layout.addWidget(banner)

        main_row = QHBoxLayout(); main_row.setSpacing(16)

        # patient selector panel
        sel_panel, sl = _panel("👤  Вибір пацієнта")
        sel_row = QHBoxLayout()
        self.patient_box = QComboBox()
        self.patient_box.currentIndexChanged.connect(lambda *_: self._load_patient())
        refresh_btn = QPushButton("↻"); refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(40); refresh_btn.clicked.connect(self.refresh)
        sel_row.addWidget(self.patient_box, 1); sel_row.addWidget(refresh_btn)
        sl.addLayout(sel_row)
        self.patient_info = QLabel("Оберіть пацієнта зі списку")
        self.patient_info.setStyleSheet(
            "color:#475569; background:#f8fafc; border-radius:8px; padding:8px 10px; font-size:12px;")
        self.patient_info.setWordWrap(True)
        sl.addWidget(self.patient_info)
        sl.addStretch(1)
        main_row.addWidget(sel_panel, 1)

        # thresholds form panel
        form_panel, fl = _panel("⚙️  Цільові показники")
        hint = QLabel("Ці значення використовуються для оцінки відхилень у вимірюваннях пацієнта.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#64748b; font-size:12px; background:#f8fafc; border-radius:8px; padding:8px 10px;")
        fl.addWidget(hint)

        form = QFormLayout(); form.setVerticalSpacing(10); form.setHorizontalSpacing(16)
        self.p_sys = QSpinBox(); self.p_sys.setRange(80, 200); self.p_sys.setSuffix(" мм рт.ст.")
        self.p_dia = QSpinBox(); self.p_dia.setRange(50, 130); self.p_dia.setSuffix(" мм рт.ст.")
        self.p_pulse = QSpinBox(); self.p_pulse.setRange(40, 150); self.p_pulse.setSuffix(" уд/хв")
        self.p_age = QSpinBox(); self.p_age.setRange(1, 120)
        form.addRow("🩺 Систолічний:", self.p_sys)
        form.addRow("🩺 Діастолічний:", self.p_dia)
        form.addRow("💓 Пульс:", self.p_pulse)
        form.addRow("🎂 Вік:", self.p_age)
        fl.addLayout(form)

        save_btn = QPushButton("💾  Зберегти для пацієнта")
        save_btn.setObjectName("primaryButton"); save_btn.clicked.connect(self._save_patient)
        fl.addWidget(save_btn)
        fl.addStretch(1)
        main_row.addWidget(form_panel, 1)
        layout.addLayout(main_row)

    def refresh(self) -> None:
        self.patient_box.blockSignals(True)
        self.patient_box.clear()
        for p in self._auth.list_patients():
            self.patient_box.addItem(p.full_name, p.id)
        self.patient_box.blockSignals(False)
        self._load_patient()

    def _load_patient(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            self.patient_info.setText("Оберіть пацієнта зі списку"); return
        self.patient_info.setText(
            f"Логін: {patient.username}  ·  Вік: {patient.age or '—'}  ·  "
            f"Поточні цілі: {patient.target_systolic}/{patient.target_diastolic}, пульс {patient.target_pulse}"
        )
        self.p_sys.setValue(patient.target_systolic)
        self.p_dia.setValue(patient.target_diastolic)
        self.p_pulse.setValue(patient.target_pulse)
        self.p_age.setValue(patient.age or 30)

    def _save_patient(self) -> None:
        pid = self.patient_box.currentData()
        patient = self._auth.get_user(pid) if pid is not None else None
        if not patient:
            QMessageBox.warning(self, "Увага", "Оберіть пацієнта."); return
        self._auth.update_user_thresholds(
            patient.id, self.p_sys.value(), self.p_dia.value(),
            self.p_pulse.value(), self.p_age.value())
        self._load_patient()
        QMessageBox.information(self, "Готово", "Пороги пацієнта оновлено.")


class DoctorReportPage(QWidget):
    def __init__(self, storage: PostgresStorage, get_patient: Callable[[], Optional[User]]):
        super().__init__()
        self.storage = storage
        self.get_patient = get_patient

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("📄  Формування звіту"); t.setObjectName("bannerTitle")
        s = QLabel("HTML-звіт містить вимірювання, рекомендації лікаря та автоматичну аналітику.")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        layout.addWidget(banner)

        panel, vl = _panel("⚙️  Налаштування звіту")
        desc = QLabel(
            "Звіт генерується для пацієнта, обраного на вкладці «Дані».\n"
            "Якщо пацієнт не обраний, спочатку перейдіть на вкладку «Пацієнти» та оберіть його."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color:#475569; font-size:13px; background:#f8fafc; border-radius:8px; padding:10px 12px;")
        vl.addWidget(desc)

        btn = QPushButton("📥  Згенерувати та зберегти HTML-звіт")
        btn.setObjectName("primaryButton"); btn.clicked.connect(self._generate)
        vl.addWidget(btn)
        vl.addStretch(1)
        layout.addWidget(panel)

    def _generate(self) -> None:
        patient = self.get_patient()
        if not patient:
            QMessageBox.warning(self, "Увага", "Оберіть пацієнта на вкладці «Пацієнти»."); return
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт", f"report_{patient.username}.html", "HTML (*.html)")
        if not path: return
        measurements = self.storage.get_measurements(patient.id)
        doctor_recs   = self.storage.get_doctor_recommendations(patient.id)
        auto_recs     = generate_recommendations(measurements)
        html = build_doctor_report_html(patient, measurements, doctor_recs, auto_recs)
        save_doctor_report(path, html)
        QMessageBox.information(self, "Готово", f"Звіт збережено:\n{path}")


# ─── Doctor Profile page ──────────────────────────────────────────────────────

class DoctorProfilePage(QWidget):
    """Профіль лікаря — редагування особистих даних та зміна пароля."""

    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage
        self._auth = AuthService()
        self._user: Optional[User] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(18)

        # banner
        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("👤  Профіль лікаря"); t.setObjectName("bannerTitle")
        s = QLabel("Особисті дані та зміна пароля облікового запису")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        root.addWidget(banner)

        row = QHBoxLayout(); row.setSpacing(16)

        # ── left: personal info ───────────────────────────────────────────
        info_panel, il = _panel("🪪  Особисті дані")
        form = QFormLayout(); form.setVerticalSpacing(10); form.setHorizontalSpacing(16)

        self.username_lbl = QLabel()
        self.username_lbl.setStyleSheet("color:#4f46e5; font-weight:600;")
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Прізвище Ім'я По батькові")
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@mail.com  (необов'язково)")
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setSpecialValueText("—")
        self.age_spin.setValue(0)

        form.addRow("Логін:", self.username_lbl)
        form.addRow("ПІБ:", self.full_name_edit)
        form.addRow("Ел. пошта:", self.email_edit)
        form.addRow("Вік:", self.age_spin)
        il.addLayout(form)

        save_btn = QPushButton("💾  Зберегти дані")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_info)
        il.addWidget(save_btn)
        il.addStretch(1)
        row.addWidget(info_panel, 1)

        # ── right: change password ────────────────────────────────────────
        pass_panel, pl = _panel("🔒  Зміна пароля")
        pform = QFormLayout(); pform.setVerticalSpacing(10); pform.setHorizontalSpacing(16)

        self.cur_pass = QLineEdit(); self.cur_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.cur_pass.setPlaceholderText("Поточний пароль")
        self.new_pass = QLineEdit(); self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pass.setPlaceholderText("Мін. 8 символів")
        self.conf_pass = QLineEdit(); self.conf_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.conf_pass.setPlaceholderText("Повторіть новий пароль")

        pform.addRow("Поточний пароль:", self.cur_pass)
        pform.addRow("Новий пароль:", self.new_pass)
        pform.addRow("Підтвердження:", self.conf_pass)
        pl.addLayout(pform)

        change_btn = QPushButton("🔑  Змінити пароль")
        change_btn.setObjectName("primaryButton")
        change_btn.clicked.connect(self._change_password)
        pl.addWidget(change_btn)
        pl.addStretch(1)
        row.addWidget(pass_panel, 1)

        root.addLayout(row)

    def refresh(self) -> None:
        fresh = self._auth.get_user(self.storage.user.id)
        if fresh:
            self._user = fresh
            self.username_lbl.setText(fresh.username)
            self.full_name_edit.setText(fresh.full_name)
            self.email_edit.setText(fresh.email or "")
            self.age_spin.setValue(fresh.age or 0)

    def _save_info(self) -> None:
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
        self._user = self._auth.get_user(self._user.id)
        QMessageBox.information(self, "Готово", "Особисті дані оновлено.")

    def _change_password(self) -> None:
        if not self._user:
            return
        cur = self.cur_pass.text()
        new = self.new_pass.text()
        conf = self.conf_pass.text()
        if not cur:
            QMessageBox.warning(self, "Помилка", "Введіть поточний пароль."); return
        if not new:
            QMessageBox.warning(self, "Помилка", "Введіть новий пароль."); return
        if new != conf:
            QMessageBox.warning(self, "Помилка", "Паролі не збігаються."); return
        if not self._auth.login(self._user.username, cur):
            QMessageBox.warning(self, "Помилка", "Поточний пароль невірний."); return
        try:
            self._auth.reset_password(self._user.id, new)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc))
            return
        self.cur_pass.clear(); self.new_pass.clear(); self.conf_pass.clear()
        QMessageBox.information(self, "Готово", "Пароль змінено.")


# ─── Admin pages ───────────────────────────────────────────────────────────────

class _EditUserDialog(QWidget):
    def __init__(self, user: User, auth: AuthService, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.setWindowTitle(f"✏️  Редагувати: {user.username}")
        self.setMinimumWidth(440)
        self._auth = auth
        self._user = user
        self.setStyleSheet(
            "QWidget { background:#f1f5fb; font-family:'Segoe UI Variable Display','Segoe UI',sans-serif; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        hdr = QLabel(f"Редагування: {user.full_name}")
        hdr.setStyleSheet("font-size:15px; font-weight:700; color:#0f172a;")
        root.addWidget(hdr)

        frame = QFrame(); frame.setObjectName("panel")
        fl = QFormLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setVerticalSpacing(10); fl.setHorizontalSpacing(16)

        self.name_edit  = QLineEdit(user.full_name)
        self.email_edit = QLineEdit(user.email or "")
        self.email_edit.setPlaceholderText("Необов'язково")
        self.age_spin   = QSpinBox(); self.age_spin.setRange(0, 120)
        self.age_spin.setSpecialValueText("—"); self.age_spin.setValue(user.age or 0)
        self.role_box   = QComboBox()
        for lbl, val in [("Пацієнт", ROLE_PATIENT), ("Лікар", ROLE_DOCTOR), ("Адміністратор", ROLE_ADMIN)]:
            self.role_box.addItem(lbl, val)
        self.role_box.setCurrentIndex(
            [ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN].index(user.role)
            if user.role in (ROLE_PATIENT, ROLE_DOCTOR, ROLE_ADMIN) else 0)
        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("Порожньо — без змін")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)

        fl.addRow("ПІБ:", self.name_edit)
        fl.addRow("Ел. пошта:", self.email_edit)
        fl.addRow("Вік:", self.age_spin)
        fl.addRow("Роль:", self.role_box)
        fl.addRow("Новий пароль:", self.new_pass)
        root.addWidget(frame)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾  Зберегти")
        save_btn.setStyleSheet(
            "QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #6366f1,stop:1 #7c3aed);color:white;border:none;border-radius:10px;"
            "font-size:13px;font-weight:700;min-height:38px;padding:0 20px;}"
            "QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #4f46e5,stop:1 #6d28d9);}"
        )
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.setStyleSheet(
            "QPushButton{background:#f1f5f9;color:#475569;border:1.5px solid #e2e8f0;"
            "border-radius:10px;font-size:13px;min-height:38px;padding:0 20px;}"
            "QPushButton:hover{background:#e2e8f0;}"
        )
        cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(save_btn); btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "ПІБ не може бути порожнім."); return
        try:
            self._auth.update_user(self._user.id, name, self.role_box.currentData(),
                                   self.age_spin.value() or None,
                                   self.email_edit.text().strip() or None)
            if self.new_pass.text():
                self._auth.reset_password(self._user.id, self.new_pass.text())
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc)); return
        QMessageBox.information(self, "Готово", "Дані оновлено.")
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # banner
        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("🛡️  Управління користувачами"); t.setObjectName("bannerTitle")
        s = QLabel("Перегляд, редагування, блокування та створення облікових записів")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        layout.addWidget(banner)

        main_row = QHBoxLayout(); main_row.setSpacing(16)

        # ── left: users table ─────────────────────────────────────────────
        tbl_panel, tvl = _panel("👥  Список користувачів")
        search_row = QHBoxLayout()
        self._search = QLineEdit(); self._search.setPlaceholderText("🔍  Пошук…")
        self._search.textChanged.connect(self._filter)
        refresh_btn = QPushButton("↻  Оновити"); refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(110); refresh_btn.clicked.connect(self.refresh)
        search_row.addWidget(self._search, 1); search_row.addWidget(refresh_btn)
        tvl.addLayout(search_row)

        self.table = _styled_table(6, ["👤 ПІБ", "🔑 Логін", "📧 Email", "🏷 Роль", "🎂 Вік", "🔘 Статус"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        tvl.addWidget(self.table)

        act_row = QHBoxLayout()
        edit_btn = QPushButton("✏️  Редагувати"); edit_btn.setObjectName("secondaryButton")
        edit_btn.clicked.connect(self._edit_selected)
        self.toggle_btn = QPushButton("🚫  Деактивувати"); self.toggle_btn.setObjectName("dangerButton")
        self.toggle_btn.clicked.connect(self._toggle_selected)
        act_row.addStretch(1); act_row.addWidget(edit_btn); act_row.addWidget(self.toggle_btn)
        tvl.addLayout(act_row)
        main_row.addWidget(tbl_panel, 3)

        # ── right: add user form ──────────────────────────────────────────
        add_panel, al = _panel("➕  Додати користувача")
        form = QFormLayout(); form.setVerticalSpacing(10); form.setHorizontalSpacing(16)
        self.new_login = QLineEdit(); self.new_login.setPlaceholderText("Обов'язково")
        self.new_pass  = QLineEdit(); self.new_pass.setPlaceholderText("Мін. 8 символів, велика+цифра")
        self.new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_name  = QLineEdit(); self.new_name.setPlaceholderText("ПІБ")
        self.new_email = QLineEdit(); self.new_email.setPlaceholderText("Необов'язково")
        self.new_age   = QSpinBox(); self.new_age.setRange(0, 120)
        self.new_age.setSpecialValueText("—"); self.new_age.setValue(0)
        self.new_role  = QComboBox()
        for lbl, val in [("Пацієнт", ROLE_PATIENT), ("Лікар", ROLE_DOCTOR), ("Адміністратор", ROLE_ADMIN)]:
            self.new_role.addItem(lbl, val)
        form.addRow("Логін:", self.new_login)
        form.addRow("Пароль:", self.new_pass)
        form.addRow("ПІБ:", self.new_name)
        form.addRow("Email:", self.new_email)
        form.addRow("Вік:", self.new_age)
        form.addRow("Роль:", self.new_role)
        al.addLayout(form)
        add_btn = QPushButton("➕  Додати користувача"); add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_user)
        al.addWidget(add_btn); al.addStretch(1)
        main_row.addWidget(add_panel, 2)

        layout.addLayout(main_row)

    def refresh(self) -> None:
        self._users = self._auth.list_users()
        self._render(self._users)

    def _render(self, users: List[User]) -> None:
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            row_bg = QColor("#f8faff") if i % 2 else QColor("#ffffff")
            vals = [u.full_name, u.username, u.email or "—", u.role_label,
                    str(u.age) if u.age else "—",
                    "✅ Активний" if u.is_active else "🚫 Заблокований"]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter if c > 0
                                      else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                item.setBackground(row_bg)
                if c == 5:
                    item.setForeground(QColor("#16a34a") if u.is_active else QColor("#e11d48"))
                self.table.setItem(i, c, item)

    def _filter(self, text: str) -> None:
        q = text.lower()
        self._render([u for u in self._users
                      if q in u.full_name.lower() or q in u.username.lower()] if q else self._users)

    def _edit_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._users):
            QMessageBox.information(self, "Увага", "Оберіть користувача."); return
        dlg = _EditUserDialog(self._users[row], self._auth, parent=self)
        dlg.show()

    def _toggle_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._users):
            QMessageBox.information(self, "Увага", "Оберіть користувача."); return
        u = self._users[row]
        action = "деактивувати" if u.is_active else "активувати"
        if QMessageBox.question(self, "Підтвердження",
                                f"Дійсно {action} «{u.username}»?") != QMessageBox.StandardButton.Yes:
            return
        self._auth.set_user_active(u.id, not u.is_active)
        self.refresh()

    def _add_user(self) -> None:
        login = self.new_login.text().strip()
        password = self.new_pass.text()
        name = self.new_name.text().strip()
        if not login: QMessageBox.warning(self, "Помилка", "Введіть логін."); return
        if not password: QMessageBox.warning(self, "Помилка", "Введіть пароль."); return
        if not name: QMessageBox.warning(self, "Помилка", "Введіть ПІБ."); return
        try:
            self._auth.create_user(login, password, name, self.new_role.currentData(),
                                   age=self.new_age.value() or None,
                                   email=self.new_email.text().strip() or None)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка", str(exc)); return
        self.new_login.clear(); self.new_pass.clear(); self.new_name.clear()
        self.new_email.clear(); self.new_age.setValue(0)
        self.refresh()
        QMessageBox.information(self, "Готово", f"Користувача «{login}» додано.")


class AdminThresholdsPage(QWidget):
    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18)
        bt = QVBoxLayout(); bt.setSpacing(4)
        t = QLabel("⚙️  Глобальні порогові значення"); t.setObjectName("bannerTitle")
        s = QLabel("Системні ліміти АТ та пульсу, що застосовуються для всіх пацієнтів за замовчуванням.")
        s.setObjectName("bannerText"); s.setWordWrap(True)
        bt.addWidget(t); bt.addWidget(s); bl.addLayout(bt, 1)
        layout.addWidget(banner)

        main_row = QHBoxLayout(); main_row.setSpacing(16)

        # systolic panel
        sp, sl = _panel("🩺  Систолічний тиск")
        sf = QFormLayout(); sf.setVerticalSpacing(10); sf.setHorizontalSpacing(16)
        self.sys_high = QSpinBox(); self.sys_high.setRange(100, 220); self.sys_high.setSuffix(" мм рт.ст.")
        self.sys_low  = QSpinBox(); self.sys_low.setRange(60, 150);   self.sys_low.setSuffix(" мм рт.ст.")
        sf.addRow("🔴 Верхній поріг:", self.sys_high)
        sf.addRow("🟡 Нижній поріг:", self.sys_low)
        sl.addLayout(sf); sl.addStretch(1)
        main_row.addWidget(sp)

        # diastolic panel
        dp, dl = _panel("🩺  Діастолічний тиск")
        df = QFormLayout(); df.setVerticalSpacing(10); df.setHorizontalSpacing(16)
        self.dia_high = QSpinBox(); self.dia_high.setRange(60, 150); self.dia_high.setSuffix(" мм рт.ст.")
        self.dia_low  = QSpinBox(); self.dia_low.setRange(40, 100);  self.dia_low.setSuffix(" мм рт.ст.")
        df.addRow("🔴 Верхній поріг:", self.dia_high)
        df.addRow("🟡 Нижній поріг:", self.dia_low)
        dl.addLayout(df); dl.addStretch(1)
        main_row.addWidget(dp)

        # pulse panel
        pp, pl = _panel("💓  Пульс")
        pf = QFormLayout(); pf.setVerticalSpacing(10); pf.setHorizontalSpacing(16)
        self.pulse_high = QSpinBox(); self.pulse_high.setRange(60, 200); self.pulse_high.setSuffix(" уд/хв")
        self.pulse_low  = QSpinBox(); self.pulse_low.setRange(30, 100);  self.pulse_low.setSuffix(" уд/хв")
        pf.addRow("🔴 Верхній поріг:", self.pulse_high)
        pf.addRow("🟡 Нижній поріг:", self.pulse_low)
        pl.addLayout(pf); pl.addStretch(1)
        main_row.addWidget(pp)
        layout.addLayout(main_row)

        save_row = QHBoxLayout()
        save_btn = QPushButton("💾  Зберегти глобальні пороги"); save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_global)
        save_row.addStretch(1); save_row.addWidget(save_btn)
        layout.addLayout(save_row)
        layout.addStretch(1)

    def refresh(self) -> None:
        t = self.storage.get_system_thresholds()
        self.sys_high.setValue(t.systolic_high);  self.sys_low.setValue(t.systolic_low)
        self.dia_high.setValue(t.diastolic_high); self.dia_low.setValue(t.diastolic_low)
        self.pulse_high.setValue(t.pulse_high);   self.pulse_low.setValue(t.pulse_low)

    def _save_global(self) -> None:
        self.storage.update_system_thresholds(SystemThresholds(
            self.sys_high.value(), self.dia_high.value(),
            self.sys_low.value(),  self.dia_low.value(),
            self.pulse_high.value(), self.pulse_low.value()))
        QMessageBox.information(self, "Готово", "Глобальні пороги збережено.")


class PatientRecommendationsView(QWidget):
    """Перегляд рекомендацій лікаря для пацієнта."""

    def __init__(self, storage: PostgresStorage):
        super().__init__()
        self.storage = storage

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        # banner
        banner = QFrame(); banner.setObjectName("topBanner")
        bl = QHBoxLayout(banner); bl.setContentsMargins(24, 18, 24, 18); bl.setSpacing(20)
        icon_lbl = QLabel("💬")
        icon_lbl.setStyleSheet(
            "font-size:38px; background:rgba(99,102,241,0.12); border-radius:14px;"
            "padding:6px 12px;"
        )
        info_col = QVBoxLayout(); info_col.setSpacing(4)
        title_lbl = QLabel("Рекомендації лікаря"); title_lbl.setObjectName("bannerTitle")
        sub_lbl = QLabel(
            "Тут відображаються індивідуальні поради вашого лікаря. "
            "Вони оновлюються кожного разу, коли лікар додає нові рекомендації."
        )
        sub_lbl.setObjectName("bannerText"); sub_lbl.setWordWrap(True)
        info_col.addWidget(title_lbl); info_col.addWidget(sub_lbl)
        refresh_btn = QPushButton("↻  Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(110)
        refresh_btn.clicked.connect(self.refresh)
        bl.addWidget(icon_lbl); bl.addLayout(info_col, 1); bl.addWidget(refresh_btn)
        layout.addWidget(banner)

        # scrollable card area
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(12)
        self._cards_layout.addStretch(1)
        scroll.setWidget(self._cards_widget)
        layout.addWidget(scroll, 1)

    def refresh(self) -> None:
        # clear previous cards (keep the stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        recs = self.storage.get_doctor_recommendations_with_doctor(self.storage.user.id)

        if not recs:
            empty = QFrame()
            empty.setStyleSheet(
                "QFrame { background: #fafaff; border: 1.5px dashed #c7d2fe;"
                " border-radius: 16px; }"
            )
            ev = QVBoxLayout(empty); ev.setContentsMargins(40, 40, 40, 40); ev.setSpacing(10)
            ev.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon = QLabel("🩺"); icon.setStyleSheet("font-size:40px; background:transparent;")
            icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg = QLabel("Поки що лікар не залишив рекомендацій.\nВони з'являться тут, як тільки лікар їх додасть.")
            msg.setStyleSheet("color:#94a3b8; font-size:13px; background:transparent;")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter); msg.setWordWrap(True)
            ev.addWidget(icon); ev.addWidget(msg)
            self._cards_layout.insertWidget(0, empty)
            return

        _GRADIENTS = [
            ("stop:0 #eef2ff, stop:1 #e0e7ff", "#6366f1"),
            ("stop:0 #f0fdf4, stop:1 #dcfce7", "#16a34a"),
            ("stop:0 #fff7ed, stop:1 #ffedd5", "#ea580c"),
            ("stop:0 #fdf4ff, stop:1 #f3e8ff", "#9333ea"),
            ("stop:0 #eff6ff, stop:1 #dbeafe", "#2563eb"),
        ]
        total = len(recs)
        for idx, (rec_text, doc_name, doc_email) in enumerate(recs):
            grad, accent = _GRADIENTS[idx % len(_GRADIENTS)]
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, {grad});"
                f" border: 1.5px solid {accent}22; border-radius: 14px; }}"
            )
            cv = QVBoxLayout(card); cv.setContentsMargins(18, 16, 18, 16); cv.setSpacing(8)

            # header row: number + doctor info
            hdr = QHBoxLayout(); hdr.setSpacing(10)
            num_lbl = QLabel(f"#{total - idx}")
            num_lbl.setStyleSheet(
                f"color:{accent}; font-size:11px; font-weight:700; background:transparent;"
            )
            hdr.addWidget(num_lbl)
            hdr.addStretch(1)

            # doctor badge
            doc_info = f"👨‍⚕️  {doc_name}"
            if doc_email:
                doc_info += f"  ·  ✉️  {doc_email}"
            doc_lbl = QLabel(doc_info)
            doc_lbl.setStyleSheet(
                f"color:{accent}; font-size:11.5px; font-weight:600; background:transparent;"
            )
            hdr.addWidget(doc_lbl)
            cv.addLayout(hdr)

            # divider
            div = QFrame(); div.setFixedHeight(1)
            div.setStyleSheet(f"background:{accent}33; border:none;")
            cv.addWidget(div)

            # recommendation text
            text_lbl = QLabel(rec_text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(
                "color:#1e293b; font-size:13.5px; background:transparent;"
            )
            cv.addWidget(text_lbl)
            self._cards_layout.insertWidget(idx, card)
