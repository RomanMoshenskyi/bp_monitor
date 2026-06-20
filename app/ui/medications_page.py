"""Medications Page - for managing patient medications."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QSpinBox, QTextEdit, QComboBox,
    QCheckBox, QGroupBox, QFrame
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
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        header.addStretch()
        
        # Add button
        self._add_btn = QPushButton("➕ Додати ліки")
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
        
        self._selected_label = QLabel("Оберіть ліки для дій")
        self._selected_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        action_layout.addWidget(self._selected_label)
        action_layout.addStretch()
        
        self._intake_btn = QPushButton("✓ Прийняв")
        self._intake_btn.setEnabled(False)
        self._intake_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#10b981;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#059669;}")
        self._intake_btn.clicked.connect(self._on_intake_selected)
        action_layout.addWidget(self._intake_btn)
        
        self._delete_btn = QPushButton("✕ Видалити")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#f43f5e;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#e11d48;}")
        self._delete_btn.clicked.connect(self._on_delete_selected)
        action_layout.addWidget(self._delete_btn)
        
        layout.addWidget(self._action_bar)
        
        # Medications table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Назва", "Дозування", "Частота", "Статус", "Примітки"
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
            
            # Store medication ID in item for selection handling
            self._table.item(i, 0).setData(Qt.ItemDataRole.UserRole, med.id)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        selected_items = self._table.selectedItems()
        if not selected_items:
            self._selected_label.setText("Оберіть ліки для дій")
            self._intake_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._selected_medication_id = None
            return
        
        # Get medication ID from first column
        self._selected_medication_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        medication = self._view_model.get_medication(self._selected_medication_id)
        
        if medication:
            self._selected_label.setText(f"Обрано: {medication.name}")
            self._intake_btn.setEnabled(medication.is_active)
            self._delete_btn.setEnabled(True)
    
    def _on_intake_selected(self):
        """Record intake for selected medication."""
        if self._selected_medication_id:
            self._on_intake(self._selected_medication_id)
    
    def _on_delete_selected(self):
        """Delete selected medication."""
        if self._selected_medication_id:
            self._on_delete(self._selected_medication_id)
        
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
