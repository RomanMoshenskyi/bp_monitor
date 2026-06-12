"""Dashboard Page with ViewModel integration (MVVM pattern)."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)
from PyQt6.QtCore import Qt

from app.presentation.view_models import DashboardViewModel
from app.widgets import GlassCard, PressureGauge, SectionTitle


class DashboardPageRefactored(QWidget):
    """
    Dashboard page using MVVM pattern.
    
    Refactored from original dashboard_page.py to use DashboardViewModel.
    """
    
    def __init__(self, view_model: DashboardViewModel):
        super().__init__()
        self._view_model = view_model
        
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self._view_model.load()
    
    def _setup_ui(self):
        """Setup UI components."""
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(18)
        
        # Loading indicator
        self._loading_bar = QProgressBar()
        self._loading_bar.setRange(0, 0)  # Indeterminate
        self._loading_bar.setVisible(False)
        main.addWidget(self._loading_bar)
        
        # Error label
        self._error_label = QLabel()
        self._error_label.setObjectName("errorLabel")
        self._error_label.setVisible(False)
        self._error_label.setStyleSheet("color: red; padding: 10px;")
        main.addWidget(self._error_label)
        
        # Banner with gauge
        banner = QFrame()
        banner.setObjectName("topBanner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(24, 22, 24, 22)
        banner_layout.setSpacing(18)
        
        # Title section
        banner_text_box = QVBoxLayout()
        
        # Welcome message with user name
        self._welcome_label = QLabel(f"Вітаємо, {self._view_model.current_user_name}")
        self._welcome_label.setObjectName("welcomeLabel")
        banner_text_box.addWidget(self._welcome_label)
        
        title = QLabel("Розумний моніторинг артеріального тиску")
        title.setObjectName("bannerTitle")
        banner_text_box.addWidget(title)
        
        # Status text
        self._status_text = QLabel(
            "Завантаження даних..." if self._view_model.is_loading else "Готово"
        )
        self._status_text.setObjectName("bannerText")
        self._status_text.setWordWrap(True)
        banner_text_box.addWidget(self._status_text)
        
        banner_layout.addLayout(banner_text_box, 3)
        
        # Pressure gauge
        self._gauge = PressureGauge()
        banner_layout.addWidget(self._gauge, 2)
        
        main.addWidget(banner)
        
        # Stats cards
        self._cards_layout = QGridLayout()
        self._cards_layout.setSpacing(16)
        
        # Latest measurement card
        self._latest_card = GlassCard("Останнє вимірювання", "—/—")
        self._cards_layout.addWidget(self._latest_card, 0, 0)
        
        # Average systolic card
        self._avg_sys_card = GlassCard("Середній систолічний", "—")
        self._cards_layout.addWidget(self._avg_sys_card, 0, 1)
        
        # Average diastolic card
        self._avg_dia_card = GlassCard("Середній діастолічний", "—")
        self._cards_layout.addWidget(self._avg_dia_card, 0, 2)
        
        # Total measurements card
        self._count_card = GlassCard("Вимірювань за тиждень", "—")
        self._cards_layout.addWidget(self._count_card, 1, 0)
        
        # Status card
        self._status_card = GlassCard("Статус", "—")
        self._cards_layout.addWidget(self._status_card, 1, 1)
        
        # Role indicator (for doctors/admins)
        if self._view_model.is_doctor or self._view_model.is_admin:
            role_text = "Лікар" if self._view_model.is_doctor else "Адміністратор"
            self._role_card = GlassCard("Роль", role_text)
            self._cards_layout.addWidget(self._role_card, 1, 2)
        
        main.addLayout(self._cards_layout)
        main.addStretch()
    
    def _connect_signals(self):
        """Connect ViewModel signals to UI slots."""
        # Loading state
        self._view_model.loading_changed.connect(self._on_loading_changed)
        
        # Errors
        self._view_model.error_occurred.connect(self._on_error)
        
        # Data updates
        self._view_model.latest_measurement_changed.connect(self._on_latest_measurement)
        self._view_model.stats_changed.connect(self._on_stats_changed)
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading indicator."""
        self._loading_bar.setVisible(is_loading)
        self._status_text.setText(
            "Завантаження даних..." if is_loading else "Готово"
        )
    
    def _on_error(self, message: str):
        """Show error message."""
        self._error_label.setText(f"Помилка: {message}")
        self._error_label.setVisible(True)
    
    def _on_latest_measurement(self, measurement):
        """Update UI with latest measurement."""
        if measurement:
            # Update gauge
            self._gauge.set_pressure(measurement.systolic, measurement.diastolic)
            
            # Update latest card
            self._latest_card.setValue(f"{measurement.systolic}/{measurement.diastolic}")
            
            # Update status card
            status_map = {
                "normal": "Норма",
                "high": "Високий",
                "low": "Низький",
            }
            status_text = status_map.get(measurement.pressure_status, "—")
            self._status_card.setValue(status_text)
            
            # Style based on status
            if measurement.pressure_status == "high":
                self._status_card.setStyleSheet("background-color: #ffebee;")
            elif measurement.pressure_status == "low":
                self._status_card.setStyleSheet("background-color: #e3f2fd;")
            else:
                self._status_card.setStyleSheet("background-color: #e8f5e9;")
    
    def _on_stats_changed(self, stats):
        """Update stats cards."""
        if stats:
            # Average systolic
            avg_sys = stats.get("avg_systolic")
            self._avg_sys_card.setValue(f"{avg_sys:.0f}" if avg_sys else "—")
            
            # Average diastolic
            avg_dia = stats.get("avg_diastolic")
            self._avg_dia_card.setValue(f"{avg_dia:.0f}" if avg_dia else "—")
            
            # Count
            count = stats.get("total_measurements", 0)
            self._count_card.setValue(str(count))
    
    def refresh(self):
        """Refresh data (public method for external calls)."""
        self._error_label.setVisible(False)
        self._view_model.load()
