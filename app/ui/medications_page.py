"""Medications Page - for managing patient medications."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QSpinBox, QTextEdit, QComboBox,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt

from app.presentation.view_models import MedicationsViewModel


class MedicationsPage(QWidget):
    """Medications management page."""
    
    def __init__(self, view_model: MedicationsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_medications()
    
    def _setup_ui(self):
        """Setup page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Управління ліками")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        # Add button
        self._add_btn = QPushButton("➕ Додати ліки")
        self._add_btn.setObjectName("primaryButton")
        self._add_btn.clicked.connect(self._on_add_clicked)
        header.addWidget(self._add_btn)
        
        layout.addLayout(header)
        
        # Medications table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Назва", "Дозування", "Частота", "Статус", "Примітки", "Дії"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)
        
        # Status label
        self._status_label = QLabel("Завантаження...")
        layout.addWidget(self._status_label)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.medications_changed.connect(self._on_medications_changed)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
    
    def _on_medications_changed(self, medications):
        """Update table with medications."""
        self._table.setRowCount(len(medications))
        
        for i, med in enumerate(medications):
            self._table.setItem(i, 0, QTableWidgetItem(med.name))
            self._table.setItem(i, 1, QTableWidgetItem(f"{med.dosage} {med.unit}"))
            self._table.setItem(i, 2, QTableWidgetItem(med.frequency))
            
            status = "Активно" if med.is_active else "Неактивно"
            status_item = QTableWidgetItem(status)
            self._table.setItem(i, 3, status_item)
            
            self._table.setItem(i, 4, QTableWidgetItem(med.notes or ""))
            
            # Action buttons
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            
            intake_btn = QPushButton("✓ Прийняв")
            intake_btn.setProperty("medication_id", med.id)
            intake_btn.clicked.connect(lambda checked, mid=med.id: self._on_intake(mid))
            actions_layout.addWidget(intake_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setProperty("medication_id", med.id)
            delete_btn.clicked.connect(lambda checked, mid=med.id: self._on_delete(mid))
            actions_layout.addWidget(delete_btn)
            
            self._table.setCellWidget(i, 5, actions)
        
        self._status_label.setText(f"Всього ліків: {len(medications)}")
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._add_btn.setEnabled(not is_loading)
        self._status_label.setText("Завантаження..." if is_loading else "")
    
    def _on_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_add_clicked(self):
        """Show add medication dialog."""
        dialog = AddMedicationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._view_model.add_medication(**data)
    
    def _on_intake(self, medication_id: int):
        """Record medication intake."""
        self._view_model.record_intake(medication_id)
    
    def _on_delete(self, medication_id: int):
        """Delete medication."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Видалити це ліки?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_medication(medication_id)


class AddMedicationDialog(QDialog):
    """Dialog for adding new medication."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Нові ліки")
        self.setMinimumWidth(350)
        
        layout = QFormLayout(self)
        
        # Name
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Наприклад: Еналаприл")
        layout.addRow("Назва:*", self._name_input)
        
        # Dosage
        self._dosage_input = QLineEdit()
        self._dosage_input.setPlaceholderText("Наприклад: 10")
        layout.addRow("Дозування:*", self._dosage_input)
        
        # Unit
        self._unit_combo = QComboBox()
        self._unit_combo.addItems(["мг", "г", "мл", "таблетки", "капсули"])
        layout.addRow("Одиниця:*", self._unit_combo)
        
        # Frequency
        self._frequency_input = QLineEdit()
        self._frequency_input.setPlaceholderText("Наприклад: 2 рази на день")
        layout.addRow("Частота прийому:*", self._frequency_input)
        
        # Notes
        self._notes_input = QTextEdit()
        self._notes_input.setMaximumHeight(60)
        self._notes_input.setPlaceholderText("Додаткові примітки...")
        layout.addRow("Примітки:", self._notes_input)
        
        # Active checkbox
        self._active_check = QCheckBox("Активно")
        self._active_check.setChecked(True)
        layout.addRow(self._active_check)
        
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
            "name": self._name_input.text(),
            "dosage": self._dosage_input.text(),
            "unit": self._unit_combo.currentText(),
            "frequency": self._frequency_input.text(),
            "notes": self._notes_input.toPlainText(),
            "is_active": self._active_check.isChecked(),
        }
