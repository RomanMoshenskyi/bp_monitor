from __future__ import annotations

import uuid
from typing import Callable, List

from PyQt6.QtCore import QDateTime, Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..analytics import measurement_to_row
from ..models import Measurement
from ..weather import city_names, detect_city_by_ip, fetch_atmospheric_pressure_mmhg
from ..widgets import SectionTitle


_PAGE_SIZE = 20


class MeasurementsPage(QWidget):
    def __init__(self, add_callback: Callable, delete_callback: Callable):
        super().__init__()
        self.add_callback = add_callback
        self.delete_callback = delete_callback
        self.measurements: List[Measurement] = []
        self._all_measurements: List[Measurement] = []
        self._current_page: int = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        top = QHBoxLayout()
        top.setSpacing(16)

        form_panel = QFrame()
        form_panel.setObjectName("panel")
        form_layout = QVBoxLayout(form_panel)
        form_layout.setContentsMargins(18, 16, 18, 18)
        form_layout.setSpacing(14)
        form_layout.addWidget(SectionTitle("Додати вимірювання"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(12)

        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_edit.setCalendarPopup(True)

        self.systolic_spin = QSpinBox()
        self.systolic_spin.setRange(60, 240)
        self.systolic_spin.setValue(120)
        self.diastolic_spin = QSpinBox()
        self.diastolic_spin.setRange(40, 150)
        self.diastolic_spin.setValue(80)
        self.pulse_spin = QSpinBox()
        self.pulse_spin.setRange(35, 220)
        self.pulse_spin.setValue(72)
        self.atm_spin = QSpinBox()
        self.atm_spin.setRange(680, 810)
        self.atm_spin.setValue(745)
        self.city_box = QComboBox()
        self.city_box.addItems(city_names())
        self.geo_btn = QPushButton("📍")
        self.geo_btn.setFixedWidth(40)
        self.geo_btn.setToolTip(
            "Визначити місто за вашим місцезнаходженням (через інтернет / IP)"
        )
        self.geo_btn.setObjectName("secondaryButton")
        self.geo_btn.clicked.connect(lambda: self._detect_my_city(silent=False))
        self._geo_detected = False
        self.fetch_atm_btn = QPushButton("Отримати атм. тиск (API)")
        self.fetch_atm_btn.setObjectName("secondaryButton")
        self.fetch_atm_btn.clicked.connect(self._fetch_atmospheric)
        self.mood_box = QComboBox()
        self.mood_box.addItems(
            ["Спокійний", "Робочий день", "Стрес", "Після тренування", "Незадовільне самопочуття"]
        )
        self.activity_box = QComboBox()
        self.activity_box.addItems(["Низька", "Середня", "Висока"])
        self.medication_check = QCheckBox("Прийом ліків перед вимірюванням")
        self.notes_edit = QTextEdit()
        self.notes_edit.setFixedHeight(90)
        self.notes_edit.setPlaceholderText(
            "Коротка примітка про стан, час доби, фізичну активність тощо"
        )

        form.addRow("Дата і час:", self.datetime_edit)
        form.addRow("Систолічний:", self.systolic_spin)
        form.addRow("Діастолічний:", self.diastolic_spin)
        form.addRow("Пульс:", self.pulse_spin)
        city_row = QHBoxLayout()
        city_row.addWidget(self.city_box, 1)
        city_row.addWidget(self.geo_btn)
        form.addRow("Місто:", city_row)
        QTimer.singleShot(400, lambda: self._detect_my_city(silent=True))
        atm_row = QHBoxLayout()
        atm_row.addWidget(self.atm_spin)
        atm_row.addWidget(self.fetch_atm_btn)
        form.addRow("Атм. тиск (мм рт. ст.):", atm_row)
        form.addRow("Стан:", self.mood_box)
        form.addRow("Активність:", self.activity_box)
        form.addRow("", self.medication_check)
        form.addRow("Примітки:", self.notes_edit)

        form_layout.addLayout(form)

        buttons = QHBoxLayout()
        self.add_btn = QPushButton("  ✚  Зберегти запис")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self._add_measurement)
        self.clear_btn = QPushButton("↺  Очистити")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self._clear_form)
        buttons.addWidget(self.add_btn)
        buttons.addWidget(self.clear_btn)
        form_layout.addLayout(buttons)

        table_panel = QFrame()
        table_panel.setObjectName("panel")
        table_layout = QVBoxLayout(table_panel)
        table_layout.setContentsMargins(18, 16, 18, 18)
        table_layout.setSpacing(14)
        table_layout.addWidget(SectionTitle("Журнал вимірювань"))

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["📅 Дата", "🩺 Тиск", "💓 Пульс", "🌡 Атм.", "😌 Стан", "💊 Ліки", "🏃 Активність", "📝 Примітки"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        hdr.setMinimumSectionSize(90)
        hdr.setDefaultSectionSize(110)
        self.table.verticalHeader().setDefaultSectionSize(42)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table_layout.addWidget(self.table)

        table_buttons = QHBoxLayout()
        self.delete_btn = QPushButton("🗑  Видалити запис")
        self.delete_btn.setObjectName("dangerButton")
        self.delete_btn.clicked.connect(self._delete_selected)

        self.prev_btn = QPushButton("‹  Назад")
        self.prev_btn.setObjectName("secondaryButton")
        self.prev_btn.setFixedWidth(90)
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn = QPushButton("Далі  ›")
        self.next_btn.setObjectName("secondaryButton")
        self.next_btn.setFixedWidth(90)
        self.next_btn.clicked.connect(self._next_page)
        self.page_label = QLabel("Сторінка 1")
        self.page_label.setStyleSheet("color:#6366f1; font-size:12px; font-weight:600;")

        self.expand_btn = QPushButton("⛶  Таблиця на весь екран")
        self.expand_btn.setObjectName("secondaryButton")
        self.expand_btn.clicked.connect(self._open_fullscreen_table)

        table_buttons.addWidget(self.prev_btn)
        table_buttons.addWidget(self.page_label)
        table_buttons.addWidget(self.next_btn)
        table_buttons.addStretch(1)
        table_buttons.addWidget(self.expand_btn)
        table_buttons.addWidget(self.delete_btn)
        table_layout.addLayout(table_buttons)

        top.addWidget(form_panel, 2)
        top.addWidget(table_panel, 3)
        layout.addLayout(top)

    def _detect_my_city(self, silent: bool = False) -> None:
        city = detect_city_by_ip()
        if not city:
            if not silent:
                QMessageBox.warning(
                    self,
                    "Геолокація",
                    "Не вдалося визначити місто.\n"
                    "Перевірте інтернет або оберіть місто вручну зі списку.",
                )
            return
        idx = self.city_box.findText(city)
        if idx >= 0:
            self.city_box.setCurrentIndex(idx)
        self._geo_detected = True
        if not silent:
            QMessageBox.information(
                self,
                "Геолокація",
                f"Обрано найближче місто зі списку: «{city}».\n"
                "Точність залежить від провайдера (визначення за IP, не GPS).",
            )

    def _fetch_atmospheric(self) -> None:
        city = self.city_box.currentText()
        value = fetch_atmospheric_pressure_mmhg(city)
        if value is None:
            QMessageBox.warning(
                self,
                "Погода",
                "Не вдалося отримати дані. Перевірте інтернет або введіть тиск вручну.",
            )
            return
        self.atm_spin.setValue(value)
        QMessageBox.information(
            self, "Погода", f"Атмосферний тиск для «{city}»: {value} мм рт. ст."
        )

    def _clear_form(self) -> None:
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.systolic_spin.setValue(120)
        self.diastolic_spin.setValue(80)
        self.pulse_spin.setValue(72)
        self.atm_spin.setValue(745)
        self.mood_box.setCurrentIndex(0)
        self.activity_box.setCurrentIndex(0)
        self.medication_check.setChecked(False)
        self.notes_edit.clear()

    def _add_measurement(self) -> None:
        measurement = Measurement(
            id=uuid.uuid4().hex[:8],
            timestamp=self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm"),
            systolic=self.systolic_spin.value(),
            diastolic=self.diastolic_spin.value(),
            pulse=self.pulse_spin.value(),
            mood=self.mood_box.currentText(),
            notes=self.notes_edit.toPlainText().strip(),
            atmospheric_pressure=self.atm_spin.value(),
            medication_taken=self.medication_check.isChecked(),
            activity_level=self.activity_box.currentText(),
        )
        try:
            self.add_callback(measurement)
        except ValueError as exc:
            QMessageBox.warning(self, "Помилка валідації", str(exc))
            return
        self._clear_form()

    def _delete_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self.measurements):
            QMessageBox.information(self, "Видалення", "Спочатку виберіть запис у таблиці.")
            return
        measurement = self.measurements[row]
        answer = QMessageBox.question(
            self, "Підтвердження", f"Видалити запис від {measurement.timestamp}?"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.delete_callback(measurement.id)

    def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._render_page()

    def _next_page(self) -> None:
        total_pages = max(1, (len(self._all_measurements) + _PAGE_SIZE - 1) // _PAGE_SIZE)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._render_page()

    def _render_page(self) -> None:
        start = self._current_page * _PAGE_SIZE
        end = start + _PAGE_SIZE
        self.measurements = self._all_measurements[start:end]
        total = len(self._all_measurements)
        total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)
        self.page_label.setText(
            f"Сторінка {self._current_page + 1} / {total_pages}  ({total} записів)"
        )
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < total_pages - 1)

        _BP_STATUS_COLORS = {
            "висок": ("#fff1f2", "#e11d48"),
            "норм":  ("#f0fdf4", "#16a34a"),
            "низьк": ("#fffbeb", "#d97706"),
        }
        self.table.setRowCount(len(self.measurements))
        for row_index, measurement in enumerate(self.measurements):
            # zebra row tint
            row_bg = QColor("#f8faff") if row_index % 2 == 1 else QColor("#ffffff")
            for col_index, cell_value in enumerate(measurement_to_row(measurement)):
                item = QTableWidgetItem(cell_value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if col_index < 7 else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                item.setBackground(row_bg)
                # colour-code BP value column (col 1)
                if col_index == 1:
                    try:
                        sys_val = int(cell_value.split("/")[0])
                        if sys_val >= 140:
                            item.setForeground(QColor("#e11d48"))
                            f = QFont(); f.setBold(True); item.setFont(f)
                        elif sys_val < 100:
                            item.setForeground(QColor("#d97706"))
                        else:
                            item.setForeground(QColor("#16a34a"))
                    except Exception:
                        pass
                # colour-code medication column (col 5)
                if col_index == 5:
                    if cell_value == "Так":
                        item.setForeground(QColor("#6366f1"))
                self.table.setItem(row_index, col_index, item)

    def _open_fullscreen_table(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("📊 Історія вимірювань")
        dlg.setMinimumSize(1100, 680)
        dlg.resize(1280, 720)
        vl = QVBoxLayout(dlg)
        vl.setContentsMargins(20, 20, 20, 20)
        vl.setSpacing(14)

        hdr_row = QHBoxLayout()
        title = QLabel(f"Історія вимірювань  (всього {len(self._all_measurements)} записів)")
        title.setStyleSheet("font-size:16px; font-weight:700; color:#0f172a;")
        close_btn = QPushButton("✕  Закрити")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(dlg.close)
        hdr_row.addWidget(title)
        hdr_row.addStretch(1)
        hdr_row.addWidget(close_btn)
        vl.addLayout(hdr_row)

        big_table = QTableWidget(0, 8)
        big_table.setHorizontalHeaderLabels(
            ["📅 Дата", "🩺 Тиск", "💓 Пульс", "🌡 Атм.", "😌 Стан", "💊 Ліки", "🏃 Активність", "📝 Примітки"]
        )
        big_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        big_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        big_table.verticalHeader().setVisible(False)
        big_table.setAlternatingRowColors(True)
        big_table.setShowGrid(False)
        big_hdr = big_table.horizontalHeader()
        big_hdr.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        big_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        big_hdr.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)
        big_hdr.setDefaultSectionSize(120)
        big_table.verticalHeader().setDefaultSectionSize(42)

        big_table.setRowCount(len(self._all_measurements))
        for row_index, measurement in enumerate(self._all_measurements):
            row_bg = QColor("#f8faff") if row_index % 2 == 1 else QColor("#ffffff")
            for col_index, cell_value in enumerate(measurement_to_row(measurement)):
                item = QTableWidgetItem(cell_value)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if col_index < 7
                    else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                item.setBackground(row_bg)
                if col_index == 1:
                    try:
                        sys_val = int(cell_value.split("/")[0])
                        if sys_val >= 140:
                            item.setForeground(QColor("#e11d48"))
                            f = QFont(); f.setBold(True); item.setFont(f)
                        elif sys_val < 100:
                            item.setForeground(QColor("#d97706"))
                        else:
                            item.setForeground(QColor("#16a34a"))
                    except Exception:
                        pass
                if col_index == 5 and cell_value == "Так":
                    item.setForeground(QColor("#6366f1"))
                big_table.setItem(row_index, col_index, item)

        vl.addWidget(big_table)
        dlg.setStyleSheet(self.window().styleSheet() if self.window() else "")
        dlg.exec()

    def refresh(self, measurements: List[Measurement]) -> None:
        self._all_measurements = list(reversed(measurements))
        self._current_page = 0
        self._render_page()
