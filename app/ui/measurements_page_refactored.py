"""Measurements Page with ViewModel integration."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QSpinBox, QTextEdit, QFormLayout, QComboBox,
    QCheckBox, QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt

from app.presentation.view_models import MeasurementsViewModel
from app.application.dto import MeasurementDTO


class MeasurementsPageRefactored(QWidget):
    """Measurements page using MVVM pattern with pagination."""
    
    def __init__(self, view_model: MeasurementsViewModel):
        super().__init__()
        self._view_model = view_model
        
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self._view_model.load_measurements(0)
    
    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header with add button
        header = QHBoxLayout()
        
        self._title = QLabel("Вимірювання тиску")
        self._title.setObjectName("pageTitle")
        header.addWidget(self._title)
        
        header.addStretch()
        
        # Add button
        self._add_btn = QPushButton("+ Додати вимірювання")
        self._add_btn.setObjectName("primaryButton")
        self._add_btn.clicked.connect(self._on_add_clicked)
        header.addWidget(self._add_btn)
        
        # Refresh button
        self._refresh_btn = QPushButton("Оновити")
        self._refresh_btn.clicked.connect(self._on_refresh)
        header.addWidget(self._refresh_btn)
        
        layout.addLayout(header)
        
        # Error label
        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: red; padding: 10px;")
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)
        
        # Loading indicator
        self._loading_label = QLabel("Завантаження...")
        self._loading_label.setVisible(False)
        layout.addWidget(self._loading_label)
        
        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Дата", "Систолічний", "Діастолічний", "Пульс", "Статус", "Дії"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)
        
        # Pagination
        pagination = QHBoxLayout()
        
        self._prev_btn = QPushButton("← Назад")
        self._prev_btn.clicked.connect(self._on_prev_page)
        pagination.addWidget(self._prev_btn)
        
        pagination.addStretch()
        
        self._page_info = QLabel("Сторінка 1 з 1")
        pagination.addWidget(self._page_info)
        
        self._total_label = QLabel("(0 записів)")
        pagination.addWidget(self._total_label)
        
        pagination.addStretch()
        
        self._next_btn = QPushButton("Вперед →")
        self._next_btn.clicked.connect(self._on_next_page)
        pagination.addWidget(self._next_btn)
        
        layout.addLayout(pagination)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.loading_changed.connect(self._on_loading_changed)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.measurements_changed.connect(self._on_measurements_changed)
        self._view_model.page_info_changed.connect(self._page_info.setText)
        self._view_model.total_count_changed.connect(self._on_total_count_changed)
        self._view_model.weather_changed.connect(self._on_weather_changed)
        self._view_model.location_changed.connect(self._on_location_changed)
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._loading_label.setVisible(is_loading)
        self._add_btn.setEnabled(not is_loading)
        self._refresh_btn.setEnabled(not is_loading)
        self._prev_btn.setEnabled(not is_loading and self._view_model.has_previous_page)
        self._next_btn.setEnabled(not is_loading and self._view_model.has_next_page)
    
    def _on_error(self, message: str):
        """Show error."""
        self._error_label.setText(f"Помилка: {message}")
        self._error_label.setVisible(True)
    
    def _on_measurements_changed(self, measurements: list):
        """Update table with measurements."""
        self._error_label.setVisible(False)
        
        self._table.setRowCount(len(measurements))
        
        for row, m in enumerate(measurements):
            # Date
            date_text = m.measured_at.strftime("%d.%m.%Y %H:%M") if m.measured_at else "—"
            self._table.setItem(row, 0, QTableWidgetItem(date_text))
            
            # Systolic
            self._table.setItem(row, 1, QTableWidgetItem(str(m.systolic)))
            
            # Diastolic
            self._table.setItem(row, 2, QTableWidgetItem(str(m.diastolic)))
            
            # Pulse
            pulse_text = str(m.pulse) if m.pulse else "—"
            self._table.setItem(row, 3, QTableWidgetItem(pulse_text))
            
            # Status with color
            status_item = QTableWidgetItem(m.pressure_status.upper())
            if m.pressure_status == "high":
                status_item.setBackground(Qt.GlobalColor.red)
                status_item.setForeground(Qt.GlobalColor.white)
            elif m.pressure_status == "low":
                status_item.setBackground(Qt.GlobalColor.blue)
                status_item.setForeground(Qt.GlobalColor.white)
            elif m.pressure_status == "normal":
                status_item.setBackground(Qt.GlobalColor.green)
                status_item.setForeground(Qt.GlobalColor.white)
            self._table.setItem(row, 4, status_item)
            
            # Delete button
            delete_btn = QPushButton("Видалити")
            delete_btn.clicked.connect(lambda checked, mid=m.id: self._on_delete(mid))
            self._table.setCellWidget(row, 5, delete_btn)
        
        # Update pagination buttons
        self._prev_btn.setEnabled(self._view_model.has_previous_page)
        self._next_btn.setEnabled(self._view_model.has_next_page)
    
    def _on_total_count_changed(self, count: int):
        """Update total count."""
        self._total_label.setText(f"({count} записів)")
    
    def _on_prev_page(self):
        """Go to previous page."""
        self._view_model.previous_page()
    
    def _on_next_page(self):
        """Go to next page."""
        self._view_model.next_page()
    
    def _on_refresh(self):
        """Refresh data."""
        self._view_model.load_measurements(self._view_model.current_page)
    
    def _on_add_clicked(self):
        """Show add measurement dialog."""
        dialog = AddMeasurementDialog(self, self._view_model)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._view_model.add_measurement(
                systolic=data["systolic"],
                diastolic=data["diastolic"],
                pulse=data.get("pulse"),
                notes=data.get("notes", ""),
                city=data.get("city"),
                mood=data.get("mood"),
                activity_level=data.get("activity_level"),
                took_medication=data.get("took_medication", False),
                medication_ids=data.get("medication_ids"),
            )
    
    def _on_weather_changed(self, weather):
        """Handle weather update."""
        pass  # Dialog handles this internally
    
    def _on_location_changed(self, city):
        """Handle location update."""
        pass  # Dialog handles this internally
    
    def _on_delete(self, measurement_id: int):
        """Delete measurement."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Видалити це вимірювання?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_measurement(measurement_id)


class AddMeasurementDialog(QDialog):
    """Dialog for adding new measurement with weather, mood, activity, medication."""
    
    def __init__(self, parent=None, view_model=None):
        super().__init__(parent)
        self._view_model = view_model
        self.setWindowTitle("Нове вимірювання")
        self.setMinimumWidth(450)
        
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # === БЛОК ТИСКУ ===
        pressure_group = QGroupBox("Показники тиску")
        pressure_layout = QGridLayout()
        
        # Systolic
        self._sys_input = QSpinBox()
        self._sys_input.setRange(50, 250)
        self._sys_input.setValue(120)
        pressure_layout.addWidget(QLabel("Систолічний:"), 0, 0)
        pressure_layout.addWidget(self._sys_input, 0, 1)
        pressure_layout.addWidget(QLabel("мм рт.ст."), 0, 2)
        
        # Diastolic
        self._dia_input = QSpinBox()
        self._dia_input.setRange(30, 150)
        self._dia_input.setValue(80)
        pressure_layout.addWidget(QLabel("Діастолічний:"), 1, 0)
        pressure_layout.addWidget(self._dia_input, 1, 1)
        pressure_layout.addWidget(QLabel("мм рт.ст."), 1, 2)
        
        # Pulse
        self._pulse_input = QSpinBox()
        self._pulse_input.setRange(30, 200)
        self._pulse_input.setValue(70)
        self._pulse_input.setSpecialValueText("—")
        pressure_layout.addWidget(QLabel("Пульс:"), 2, 0)
        pressure_layout.addWidget(self._pulse_input, 2, 1)
        pressure_layout.addWidget(QLabel("уд/хв"), 2, 2)
        
        pressure_group.setLayout(pressure_layout)
        layout.addRow(pressure_group)
        
        # === БЛОК МІСЦЯ І ПОГОДИ ===
        location_group = QGroupBox("Місце та погода")
        location_layout = QHBoxLayout()
        
        # City
        self._city_input = QLineEdit()
        self._city_input.setPlaceholderText("Київ")
        self._city_input.setText(self._view_model._current_city if view_model else "Київ")
        location_layout.addWidget(QLabel("Місто:"))
        location_layout.addWidget(self._city_input)
        
        # Auto-detect button
        self._detect_btn = QPushButton("🌍")
        self._detect_btn.setToolTip("Автовизначення локації")
        self._detect_btn.clicked.connect(self._on_detect_location)
        location_layout.addWidget(self._detect_btn)
        
        # Fetch weather button
        self._weather_btn = QPushButton("🌡️")
        self._weather_btn.setToolTip("Отримати погоду")
        self._weather_btn.clicked.connect(self._on_fetch_weather)
        location_layout.addWidget(self._weather_btn)
        
        location_group.setLayout(location_layout)
        layout.addRow(location_group)
        
        # Weather display
        self._weather_label = QLabel("Тиск: невідомо")
        self._weather_label.setStyleSheet("color: gray; font-size: 12px;")
        layout.addRow(self._weather_label)
        
        # === БЛОК КОНТЕКСТУ ===
        context_group = QGroupBox("Контекст вимірювання")
        context_layout = QFormLayout()
        
        # Mood
        self._mood_combo = QComboBox()
        self._mood_combo.addItem("Спокійний", "calm")
        self._mood_combo.addItem("Робочий день", "work_day")
        self._mood_combo.addItem("Стрес", "stress")
        self._mood_combo.addItem("Відпочинок", "rest")
        context_layout.addRow("Стан/настрій:", self._mood_combo)
        
        # Activity level
        self._activity_combo = QComboBox()
        self._activity_combo.addItem("Низька", "low")
        self._activity_combo.addItem("Середня", "medium")
        self._activity_combo.addItem("Висока", "high")
        context_layout.addRow("Активність:", self._activity_combo)
        
        # Medication checkbox
        self._medication_check = QCheckBox("Прийняв ліки")
        context_layout.addRow(self._medication_check)
        
        context_group.setLayout(context_layout)
        layout.addRow(context_group)
        
        # Notes
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setPlaceholderText("Додаткові примітки...")
        layout.addRow("Примітки:", self._notes_input)
        
        # Buttons
        buttons = QHBoxLayout()
        
        self._save_btn = QPushButton("Зберегти")
        self._save_btn.setObjectName("primaryButton")
        self._save_btn.clicked.connect(self.accept)
        buttons.addWidget(self._save_btn)
        
        self._cancel_btn = QPushButton("Скасувати")
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)
        
        layout.addRow(buttons)
        
        # Connect to ViewModel signals if available
        if view_model:
            view_model.weather_changed.connect(self._on_weather_updated)
            view_model.location_changed.connect(self._on_location_updated)
            view_model.error_occurred.connect(self._on_error)
    
    def _on_detect_location(self):
        """Auto-detect location."""
        if self._view_model:
            self._view_model.detect_location()
    
    def _on_fetch_weather(self):
        """Fetch weather for current city."""
        city = self._city_input.text() or "Київ"
        if self._view_model:
            self._view_model.fetch_weather(city)
    
    def _on_weather_updated(self, weather):
        """Update weather display."""
        if weather:
            self._weather_label.setText(
                f"Тиск: {weather.pressure_mmhg} мм рт.ст. | "
                f"Темп: {weather.temperature}°C | "
                f"Вологість: {weather.humidity}%"
            )
            self._weather_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self._weather_label.setText("Тиск: не вдалося отримати дані")
            self._weather_label.setStyleSheet("color: red; font-size: 12px;")
    
    def _on_location_updated(self, city):
        """Update city field."""
        if city:
            self._city_input.setText(city)
    
    def _on_error(self, message):
        """Show error in dialog."""
        QMessageBox.warning(self, "Попередження", message)
    
    def get_data(self) -> dict:
        """Get entered data."""
        return {
            "systolic": self._sys_input.value(),
            "diastolic": self._dia_input.value(),
            "pulse": self._pulse_input.value() if self._pulse_input.value() > 0 else None,
            "notes": self._notes_input.toPlainText(),
            "city": self._city_input.text() or "Київ",
            "mood": self._mood_combo.currentData(),
            "activity_level": self._activity_combo.currentData(),
            "took_medication": self._medication_check.isChecked(),
            "medication_ids": None,  # TODO: Add medication selection UI
        }
