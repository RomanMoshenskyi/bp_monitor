"""Thresholds Page - for managing BP threshold profiles."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QSpinBox, QGroupBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

from app.presentation.view_models import ThresholdsViewModel


class ThresholdsPage(QWidget):
    """Threshold profile configuration page."""
    
    def __init__(self, view_model: ThresholdsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_profile()
    
    def _setup_ui(self):
        """Setup page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Порогові значення АТ")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Description
        desc = QLabel(
            "Налаштуйте порогові значення для визначення статусу ваших вимірювань. "
            "Значення поза цими межами будуть позначені як високі або низькі."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: gray;")
        layout.addWidget(desc)
        
        # Systolic thresholds
        sys_group = QGroupBox("Систолічний тиск (верхнє)")
        sys_layout = QHBoxLayout()
        
        sys_min_layout = QFormLayout()
        self._sys_min_input = QSpinBox()
        self._sys_min_input.setRange(70, 200)
        self._sys_min_input.setValue(90)
        self._sys_min_input.setSuffix(" мм рт.ст.")
        sys_min_layout.addRow("Мінімум:", self._sys_min_input)
        sys_layout.addLayout(sys_min_layout)
        
        sys_max_layout = QFormLayout()
        self._sys_max_input = QSpinBox()
        self._sys_max_input.setRange(100, 250)
        self._sys_max_input.setValue(140)
        self._sys_max_input.setSuffix(" мм рт.ст.")
        sys_max_layout.addRow("Максимум:", self._sys_max_input)
        sys_layout.addLayout(sys_max_layout)
        
        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)
        
        # Diastolic thresholds
        dia_group = QGroupBox("Діастолічний тиск (нижнє)")
        dia_layout = QHBoxLayout()
        
        dia_min_layout = QFormLayout()
        self._dia_min_input = QSpinBox()
        self._dia_min_input.setRange(40, 120)
        self._dia_min_input.setValue(60)
        self._dia_min_input.setSuffix(" мм рт.ст.")
        dia_min_layout.addRow("Мінімум:", self._dia_min_input)
        dia_layout.addLayout(dia_min_layout)
        
        dia_max_layout = QFormLayout()
        self._dia_max_input = QSpinBox()
        self._dia_max_input.setRange(60, 150)
        self._dia_max_input.setValue(90)
        self._dia_max_input.setSuffix(" мм рт.ст.")
        dia_max_layout.addRow("Максимум:", self._dia_max_input)
        dia_layout.addLayout(dia_max_layout)
        
        dia_group.setLayout(dia_layout)
        layout.addWidget(dia_group)
        
        # Pulse thresholds
        pulse_group = QGroupBox("Пульс (опціонально)")
        pulse_layout = QHBoxLayout()
        
        pulse_min_layout = QFormLayout()
        self._pulse_min_input = QSpinBox()
        self._pulse_min_input.setRange(30, 100)
        self._pulse_min_input.setValue(50)
        self._pulse_min_input.setSuffix(" уд/хв")
        pulse_min_layout.addRow("Мінімум:", self._pulse_min_input)
        pulse_layout.addLayout(pulse_min_layout)
        
        pulse_max_layout = QFormLayout()
        self._pulse_max_input = QSpinBox()
        self._pulse_max_input.setRange(60, 200)
        self._pulse_max_input.setValue(100)
        self._pulse_max_input.setSuffix(" уд/хв")
        pulse_max_layout.addRow("Максимум:", self._pulse_max_input)
        pulse_layout.addLayout(pulse_max_layout)
        
        pulse_group.setLayout(pulse_layout)
        layout.addWidget(pulse_group)
        
        # Status preview
        self._status_frame = QFrame()
        self._status_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self._status_layout = QVBoxLayout(self._status_frame)
        self._status_label = QLabel("Перевірка значень...")
        self._status_layout.addWidget(self._status_label)
        layout.addWidget(self._status_frame)
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        self._save_btn = QPushButton("💾 Зберегти")
        self._save_btn.setObjectName("primaryButton")
        self._save_btn.clicked.connect(self._on_save)
        buttons.addWidget(self._save_btn)
        
        self._check_btn = QPushButton("🔍 Перевірити")
        self._check_btn.clicked.connect(self._on_check)
        buttons.addWidget(self._check_btn)
        
        layout.addLayout(buttons)
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.profile_loaded.connect(self._on_profile_loaded)
        self._view_model.thresholds_saved.connect(self._on_thresholds_saved)
        self._view_model.measurement_checked.connect(self._on_measurement_checked)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
        
        # Connect inputs to check
        for input_widget in [
            self._sys_min_input, self._sys_max_input,
            self._dia_min_input, self._dia_max_input,
            self._pulse_min_input, self._pulse_max_input
        ]:
            input_widget.valueChanged.connect(self._on_input_changed)
    
    def _on_profile_loaded(self, profile):
        """Load profile values into inputs."""
        if profile:
            self._sys_min_input.setValue(profile.sys_min)
            self._sys_max_input.setValue(profile.sys_max)
            self._dia_min_input.setValue(profile.dia_min)
            self._dia_max_input.setValue(profile.dia_max)
            if profile.pulse_min:
                self._pulse_min_input.setValue(profile.pulse_min)
            if profile.pulse_max:
                self._pulse_max_input.setValue(profile.pulse_max)
    
    def _on_input_changed(self):
        """Update status preview when inputs change."""
        self._status_label.setText("Натисніть 'Перевірити' для тестування значень")
        self._status_label.setStyleSheet("color: gray;")
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._save_btn.setEnabled(not is_loading)
        self._check_btn.setEnabled(not is_loading)
    
    def _on_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_save(self):
        """Save threshold values."""
        self._view_model.save_thresholds(
            sys_min=self._sys_min_input.value(),
            sys_max=self._sys_max_input.value(),
            dia_min=self._dia_min_input.value(),
            dia_max=self._dia_max_input.value(),
            pulse_min=self._pulse_min_input.value(),
            pulse_max=self._pulse_max_input.value(),
        )
    
    def _on_thresholds_saved(self, success: bool, message: str):
        """Handle save result."""
        if success:
            QMessageBox.information(self, "Успіх", message)
        else:
            QMessageBox.warning(self, "Попередження", message)
    
    def _on_check(self):
        """Test threshold values with sample measurement."""
        # Use middle values for preview
        test_sys = (self._sys_min_input.value() + self._sys_max_input.value()) // 2
        test_dia = (self._dia_min_input.value() + self._dia_max_input.value()) // 2
        test_pulse = (self._pulse_min_input.value() + self._pulse_max_input.value()) // 2
        
        self._view_model.check_measurement(test_sys, test_dia, test_pulse)
    
    def _on_measurement_checked(self, result: dict):
        """Update status preview with check result."""
        status = result.get("overall_status", "unknown")
        
        status_messages = {
            "normal": ("✅ Значення в нормі", "color: green;"),
            "high": ("⚠️ Значення високі", "color: orange;"),
            "low": ("⚠️ Значення низькі", "color: blue;"),
        }
        
        message, style = status_messages.get(status, ("Невідомий статус", "color: gray;"))
        self._status_label.setText(message)
        self._status_label.setStyleSheet(style)
