"""Activities Page - for tracking physical activities."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QSpinBox, QTextEdit, QComboBox,
    QDateTimeEdit, QFrame
)
from PyQt6.QtCore import Qt, QDateTime

from app.presentation.view_models import ActivitiesViewModel


class ActivitiesPage(QWidget):
    """Activities tracking page."""
    
    def __init__(self, view_model: ActivitiesViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_activities()
    
    def _setup_ui(self):
        """Setup page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Журнал активності")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        header.addStretch()
        
        # Add button
        self._add_btn = QPushButton("➕ Додати активність")
        self._add_btn.setObjectName("primaryButton")
        self._add_btn.clicked.connect(self._on_add_clicked)
        header.addWidget(self._add_btn)
        
        layout.addLayout(header)
        
        # Action bar
        self._action_bar = QFrame()
        self._action_bar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fafc,stop:1 #f1f5f9); border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        action_layout = QHBoxLayout(self._action_bar)
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(8)
        
        self._selected_label = QLabel("Оберіть активність для дій")
        self._selected_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        action_layout.addWidget(self._selected_label)
        action_layout.addStretch()
        
        self._delete_btn = QPushButton("✕ Видалити")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#f43f5e;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#e11d48;}")
        self._delete_btn.clicked.connect(self._on_delete_selected)
        action_layout.addWidget(self._delete_btn)
        
        layout.addWidget(self._action_bar)
        
        # Activities table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Тип", "Тривалість", "Інтенсивність", "Калорії", "Час"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(40)
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._table)
        
        # Status label
        self._status_label = QLabel("Завантаження...")
        layout.addWidget(self._status_label)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.activities_changed.connect(self._on_activities_changed)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
    
    def _on_activities_changed(self, activities):
        """Update table with activities."""
        self._table.setRowCount(len(activities))
        
        for i, act in enumerate(activities):
            # Type
            type_display = self._get_activity_type_display(act.activity_type)
            self._table.setItem(i, 0, QTableWidgetItem(type_display))
            
            # Duration
            duration_text = f"{act.duration_minutes} хв"
            self._table.setItem(i, 1, QTableWidgetItem(duration_text))
            
            # Intensity
            intensity_map = {"low": "Низька", "medium": "Середня", "high": "Висока"}
            intensity_text = intensity_map.get(act.intensity, act.intensity)
            self._table.setItem(i, 2, QTableWidgetItem(intensity_text))
            
            # Calories
            cal_text = str(act.calories_burned) if act.calories_burned else "—"
            self._table.setItem(i, 3, QTableWidgetItem(cal_text))
            
            # Time
            time_text = act.started_at.strftime("%d.%m.%Y %H:%M") if act.started_at else "—"
            self._table.setItem(i, 4, QTableWidgetItem(time_text))
            
            # Store activity ID in item for selection handling
            self._table.item(i, 0).setData(Qt.ItemDataRole.UserRole, act.id)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        selected_items = self._table.selectedItems()
        if not selected_items:
            self._selected_label.setText("Оберіть активність для дій")
            self._delete_btn.setEnabled(False)
            self._selected_activity_id = None
            return
        
        # Get activity ID from first column
        self._selected_activity_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self._selected_label.setText("Обрано активність")
        self._delete_btn.setEnabled(True)
    
    def _on_delete_selected(self):
        """Delete selected activity."""
        if self._selected_activity_id:
            self._on_delete(self._selected_activity_id)
        
        self._status_label.setText(f"Всього записів: {len(activities)}")
    
    def _get_activity_type_display(self, activity_type: str) -> str:
        """Get display name for activity type."""
        type_map = {
            "walking": "Ходьба",
            "running": "Біг",
            "cycling": "Велосипед",
            "swimming": "Плавання",
            "gym": "Тренажерний зал",
            "yoga": "Йога",
            "sport": "Спорт",
            "other": "Інше",
        }
        return type_map.get(activity_type, activity_type)
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._add_btn.setEnabled(not is_loading)
        self._status_label.setText("Завантаження..." if is_loading else "")
    
    def _on_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_add_clicked(self):
        """Show add activity dialog."""
        dialog = AddActivityDialog(self, self._view_model)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._view_model.add_activity(**data)
    
    def _on_delete(self, activity_id: int):
        """Delete activity."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Видалити цей запис активності?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_activity(activity_id)


class AddActivityDialog(QDialog):
    """Dialog for adding new activity."""
    
    def __init__(self, parent=None, view_model=None):
        super().__init__(parent)
        self._view_model = view_model
        self.setWindowTitle("Нова активність")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        
        # Type
        self._type_combo = QComboBox()
        if view_model:
            for value, label in view_model.get_activity_types():
                self._type_combo.addItem(label, value)
        else:
            types = [
                ("walking", "Ходьба"),
                ("running", "Біг"),
                ("cycling", "Велосипед"),
                ("swimming", "Плавання"),
                ("gym", "Тренажерний зал"),
                ("yoga", "Йога"),
                ("sport", "Спорт"),
                ("other", "Інше"),
            ]
            for value, label in types:
                self._type_combo.addItem(label, value)
        layout.addRow("Тип активності:*", self._type_combo)
        
        # Duration
        self._duration_input = QSpinBox()
        self._duration_input.setRange(1, 600)
        self._duration_input.setValue(30)
        self._duration_input.setSuffix(" хв")
        layout.addRow("Тривалість:*", self._duration_input)
        
        # Intensity
        self._intensity_combo = QComboBox()
        self._intensity_combo.addItem("Низька", "low")
        self._intensity_combo.addItem("Середня", "medium")
        self._intensity_combo.addItem("Висока", "high")
        layout.addRow("Інтенсивність:", self._intensity_combo)
        
        # Calories
        self._calories_input = QSpinBox()
        self._calories_input.setRange(0, 2000)
        self._calories_input.setValue(0)
        self._calories_input.setSpecialValueText("—")
        layout.addRow("Калорії:", self._calories_input)
        
        # Date/Time
        self._datetime_input = QDateTimeEdit()
        self._datetime_input.setDateTime(QDateTime.currentDateTime())
        self._datetime_input.setCalendarPopup(True)
        layout.addRow("Час початку:", self._datetime_input)
        
        # Notes
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setPlaceholderText("Додаткові примітки...")
        layout.addRow("Примітки:", self._notes_input)
        
        # Buttons
        buttons = QHBoxLayout()
        
        self._save_btn = QPushButton("Зберегти")
        self._save_btn.clicked.connect(self.accept)
        buttons.addWidget(self._save_btn)
        
        self._cancel_btn = QPushButton("Скасувати")
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)
        
        layout.addRow(buttons)
    
    def get_data(self) -> dict:
        """Get entered data."""
        return {
            "activity_type": self._type_combo.currentData(),
            "duration_minutes": self._duration_input.value(),
            "intensity": self._intensity_combo.currentData(),
            "calories_burned": self._calories_input.value() if self._calories_input.value() > 0 else None,
            "notes": self._notes_input.toPlainText(),
            "measurement_id": None,  # Can be linked later
        }
