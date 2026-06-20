"""Doctor Prescriptions Page - Create and manage patient prescriptions."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QTextEdit, QComboBox, QDateEdit, QSpinBox,
    QGroupBox, QScrollArea, QGridLayout, QCheckBox, QTimeEdit,
    QListWidget, QListWidgetItem, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QColor

from app.presentation.view_models import PrescriptionsViewModel
from app.auth import AuthService
from app.infrastructure.orm.base import SessionLocal
from app.domain.entities import MedicationORM


class DoctorPrescriptionsPage(QWidget):
    """
    Prescription management page for doctors.
    
    Features:
    - Create prescriptions with detailed medication schedules
    - View all prescriptions created for patients
    - Cancel prescriptions
    """
    
    def __init__(self, view_model: PrescriptionsViewModel, auth_service: AuthService = None):
        super().__init__()
        self._view_model = view_model
        self._auth = auth_service or AuthService()
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_doctor_prescriptions()
    
    def _setup_ui(self):
        """Setup the page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = self._create_header()
        layout.addLayout(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        
        # Top: Prescription form
        form_panel = self._create_prescription_form()
        content_layout.addWidget(form_panel)
        
        # Bottom: Prescription history table
        history_panel = self._create_prescription_history()
        content_layout.addWidget(history_panel)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def _create_header(self) -> QHBoxLayout:
        """Create page header."""
        header = QHBoxLayout()
        
        title = QLabel(" Призначення ліків")
        title.setObjectName("pageTitle")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        header.addWidget(title)
        
        header.addStretch()
        
        # Patient indicator
        self._patient_label = QLabel("Пацієнт: не обрано")
        self._patient_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 18px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #f8fafc, stop:1 #eef2ff);
                border: 1.5px solid rgba(99,102,241,0.12);
                border-radius: 12px;
            }
        """)
        header.addWidget(self._patient_label)
        
        return header
    
    def _create_prescription_form(self) -> QWidget:
        """Create prescription creation form."""
        panel = QGroupBox(" Нове призначення")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                color: #0f172a;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 16px;
                padding: 18px;
                margin-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #4f46e5;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(14)
        
        # Medication info
        med_group = QGroupBox("Інформація про ліки")
        med_layout = QGridLayout(med_group)
        med_layout.setHorizontalSpacing(12)
        med_layout.setVerticalSpacing(10)
        
        self._med_name = QComboBox()
        self._med_name.setEditable(True)
        self._med_name.setPlaceholderText("Назва ліків*")
        self._load_medications()
        med_layout.addWidget(QLabel("Назва:*"), 0, 0)
        med_layout.addWidget(self._med_name, 0, 1)
        
        self._med_form = QComboBox()
        self._med_form.addItems(["Таблетки", "Капсули", "Сироп", "Розчин", "Мазь", "Краплі", "Інше"])
        med_layout.addWidget(QLabel("Форма:"), 0, 2)
        med_layout.addWidget(self._med_form, 0, 3)
        
        self._dosage = QLineEdit()
        self._dosage.setPlaceholderText("Напр: 10 мг, 1 таблетка*")
        med_layout.addWidget(QLabel("Дозування:*"), 1, 0)
        med_layout.addWidget(self._dosage, 1, 1)
        
        layout.addWidget(med_group)
        
        # Schedule
        sched_group = QGroupBox("Розклад прийому")
        sched_layout = QGridLayout(sched_group)
        sched_layout.setHorizontalSpacing(12)
        sched_layout.setVerticalSpacing(10)
        
        self._frequency = QSpinBox()
        self._frequency.setRange(1, 12)
        self._frequency.setValue(2)
        self._frequency.valueChanged.connect(self._update_time_inputs)
        sched_layout.addWidget(QLabel("Разів на день:*"), 0, 0)
        sched_layout.addWidget(self._frequency, 0, 1)
        
        self._duration = QSpinBox()
        self._duration.setRange(1, 365)
        self._duration.setValue(7)
        self._duration.setSuffix(" днів")
        sched_layout.addWidget(QLabel("Тривалість:*"), 0, 2)
        sched_layout.addWidget(self._duration, 0, 3)
        
        self._start_date = QDateEdit()
        self._start_date.setDate(QDate.currentDate())
        self._start_date.setCalendarPopup(True)
        sched_layout.addWidget(QLabel("Початок:*"), 1, 0)
        sched_layout.addWidget(self._start_date, 1, 1)
        
        # Time inputs container
        self._time_inputs_widget = QWidget()
        self._time_layout = QVBoxLayout(self._time_inputs_widget)
        self._time_inputs = []
        sched_layout.addWidget(self._time_inputs_widget, 2, 0, 1, 4)
        
        self._update_time_inputs()
        
        # Administration instructions
        self._with_food = QCheckBox("Приймати з їжею")
        self._before_food = QCheckBox("До їди")
        self._after_food = QCheckBox("Після їди")
        
        food_layout = QHBoxLayout()
        food_layout.addWidget(self._with_food)
        food_layout.addWidget(self._before_food)
        food_layout.addWidget(self._after_food)
        food_layout.addStretch()
        sched_layout.addLayout(food_layout, 3, 0, 1, 4)
        
        layout.addWidget(sched_group)
        
        # Additional info
        info_group = QGroupBox("Додаткова інформація")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)
        
        self._prescribed_for = QTextEdit()
        self._prescribed_for.setPlaceholderText("Для чого призначено (показання)...")
        self._prescribed_for.setMaximumHeight(60)
        info_layout.addWidget(QLabel("Показання:"))
        info_layout.addWidget(self._prescribed_for)
        
        self._instructions = QTextEdit()
        self._instructions.setPlaceholderText("Особливі інструкції...")
        self._instructions.setMaximumHeight(60)
        info_layout.addWidget(QLabel("Інструкції:"))
        info_layout.addWidget(self._instructions)
        
        layout.addWidget(info_group)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        clear_btn = QPushButton(" Очистити")
        clear_btn.clicked.connect(self._clear_form)
        actions_layout.addWidget(clear_btn)
        
        create_btn = QPushButton(" Створити призначення")
        create_btn.setObjectName("primaryButton")
        create_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 12px;
                padding: 12px 26px;
                font-weight: 700;
                font-size: 13px;
                letter-spacing: 0.2px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #059669, stop:1 #047857);
            }
        """)
        create_btn.clicked.connect(self._create_prescription)
        actions_layout.addWidget(create_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        return panel
    
    def _load_medications(self):
        """Load existing medications into the combo box."""
        db = SessionLocal()
        try:
            medications = db.query(MedicationORM).order_by(MedicationORM.name).all()
            self._med_name.clear()
            self._med_name.addItem("")  # Empty option
            for med in medications:
                display_name = f"{med.name} ({med.dosage})" if med.dosage else med.name
                self._med_name.addItem(display_name, med.id)
        finally:
            db.close()
        
        # Connect signal to auto-fill dosage when selection changes
        self._med_name.currentIndexChanged.connect(self._on_medication_selected)
    
    def _on_medication_selected(self, index):
        """Handle medication selection change - auto-fill dosage."""
        if index <= 0:  # Empty option selected
            return
        
        med_id = self._med_name.currentData()
        if med_id:
            db = SessionLocal()
            try:
                med = db.query(MedicationORM).filter(MedicationORM.id == med_id).first()
                if med and med.dosage:
                    self._dosage.setText(med.dosage)
            finally:
                db.close()
    
    def _update_time_inputs(self):
        """Update time input fields based on frequency."""
        # Clear existing widgets from time layout
        while self._time_layout.count():
            item = self._time_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        
        self._time_inputs = []
        frequency = self._frequency.value()
        
        # Default times based on frequency
        default_times = [
            ["09:00"],
            ["08:00", "20:00"],
            ["08:00", "14:00", "20:00"],
            ["08:00", "12:00", "16:00", "20:00"],
        ]
        
        times = default_times[min(frequency - 1, 3)] if frequency <= 4 else ["08:00"] * frequency
        
        for i in range(frequency):
            row = QHBoxLayout()
            label = QLabel(f"Прийом {i + 1}:")
            label.setMinimumWidth(100)
            row.addWidget(label)
            time_edit = QTimeEdit()
            time_edit.setDisplayFormat("HH:mm")
            time_edit.setMinimumWidth(120)
            
            # Set default time
            if i < len(times):
                parts = times[i].split(":")
                time_edit.setTime(QTime(int(parts[0]), int(parts[1])))
            
            self._time_inputs.append(time_edit)
            row.addWidget(time_edit)
            row.addStretch()
            self._time_layout.addLayout(row)
    
    def _create_prescription_history(self) -> QWidget:
        """Create prescription history panel."""
        panel = QGroupBox("📋 Історія призначень")
        panel.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                color: #0f172a;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 16px;
                padding: 18px;
                margin-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #4f46e5;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # Info label
        info = QLabel("Призначення для обраного пацієнта")
        info.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        layout.addWidget(info)
        
        # Action bar
        self._action_bar = QFrame()
        self._action_bar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fafc,stop:1 #f1f5f9); border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        action_layout = QHBoxLayout(self._action_bar)
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(8)
        
        self._selected_label = QLabel("Оберіть рецепт для дій")
        self._selected_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        action_layout.addWidget(self._selected_label)
        action_layout.addStretch()
        
        self._view_btn = QPushButton("👁 Переглянути")
        self._view_btn.setEnabled(False)
        self._view_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#6366f1;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#4f46e5;}")
        self._view_btn.clicked.connect(self._on_view_selected)
        action_layout.addWidget(self._view_btn)
        
        self._cancel_btn = QPushButton("✕ Скасувати")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#f43f5e;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#e11d48;}")
        self._cancel_btn.clicked.connect(self._on_cancel_selected)
        action_layout.addWidget(self._cancel_btn)
        
        layout.addWidget(self._action_bar)
        
        # Prescriptions table
        self._prescriptions_table = QTableWidget()
        self._prescriptions_table.setColumnCount(5)
        self._prescriptions_table.setHorizontalHeaderLabels([
            "№", "Ліки", "Дозування", "Період", "Статус"
        ])
        self._prescriptions_table.setMinimumHeight(250)
        self._prescriptions_table.setMaximumHeight(450)
        self._prescriptions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._prescriptions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._prescriptions_table.horizontalHeader().setMinimumSectionSize(80)
        self._prescriptions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._prescriptions_table.setAlternatingRowColors(True)
        self._prescriptions_table.verticalHeader().setVisible(False)
        self._prescriptions_table.verticalHeader().setDefaultSectionSize(36)
        self._prescriptions_table.itemSelectionChanged.connect(self._on_selection_changed)
        self._prescriptions_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._prescriptions_table, 1)
        
        return panel
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.prescriptions_changed.connect(self._on_prescriptions_changed)
        self._view_model.prescription_created.connect(self._on_prescription_created)
        self._view_model.error_occurred.connect(self._on_error)
    
    def _on_prescriptions_changed(self, prescriptions):
        """Update prescriptions table."""
        self._prescriptions_table.setRowCount(len(prescriptions))
        
        for i, rx in enumerate(prescriptions):
            self._prescriptions_table.setItem(i, 0, QTableWidgetItem(rx.prescription_number))
            self._prescriptions_table.setItem(i, 1, QTableWidgetItem(rx.medication_name))
            self._prescriptions_table.setItem(i, 2, QTableWidgetItem(rx.dosage))
            
            period_text = f"{rx.start_date.strftime('%d.%m')}"
            if rx.end_date:
                period_text += f" - {rx.end_date.strftime('%d.%m')}"
            self._prescriptions_table.setItem(i, 3, QTableWidgetItem(period_text))
            
            status_map = {
                "active": "🟢 Активно",
                "completed": "✅ Завершено",
                "cancelled": "❌ Скасовано",
                "expired": "⏰ Прострочено"
            }
            status_text = status_map.get(rx.status, rx.status)
            status_item = QTableWidgetItem(status_text)
            
            if rx.status == "active":
                status_item.setForeground(QColor("#38a169"))
            elif rx.status == "cancelled":
                status_item.setForeground(QColor("#e53e3e"))
            
            self._prescriptions_table.setItem(i, 4, status_item)
            
            # Store prescription ID in item for selection handling
            self._prescriptions_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, rx.id)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        selected_items = self._prescriptions_table.selectedItems()
        if not selected_items:
            self._selected_label.setText("Оберіть рецепт для дій")
            self._view_btn.setEnabled(False)
            self._cancel_btn.setEnabled(False)
            self._selected_prescription_id = None
            return
        
        # Get prescription ID from first column
        self._selected_prescription_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        prescription = self._view_model.get_prescription(self._selected_prescription_id)
        
        if prescription:
            self._selected_label.setText(f"Обрано: Рецепт #{prescription.prescription_number}")
            self._view_btn.setEnabled(True)
            self._cancel_btn.setEnabled(prescription.status == "active")
    
    def _on_view_selected(self):
        """View selected prescription."""
        if self._selected_prescription_id:
            self._view_prescription(self._selected_prescription_id)
    
    def _on_cancel_selected(self):
        """Cancel selected prescription."""
        if self._selected_prescription_id:
            self._cancel_prescription(self._selected_prescription_id)
    
    def _on_prescription_created(self, success, message):
        if success:
            QMessageBox.information(self, "Успіх", message)
            self._clear_form()
        else:
            QMessageBox.warning(self, "Помилка", message)
    
    def _on_error(self, message):
        QMessageBox.critical(self, "Помилка", message)
    
    def _clear_form(self):
        self._med_name.clear()
        self._dosage.clear()
        self._frequency.setValue(2)
        self._duration.setValue(7)
        self._prescribed_for.clear()
        self._instructions.clear()
        self._with_food.setChecked(False)
        self._before_food.setChecked(False)
        self._after_food.setChecked(False)
    
    def _create_prescription(self):
        med_name_text = self._med_name.currentText().strip()
        if not med_name_text:
            QMessageBox.warning(self, "Помилка", "Введіть назву ліків")
            return
        
        if not self._dosage.text().strip():
            QMessageBox.warning(self, "Помилка", "Введіть дозування")
            return
        
        # Check if medication exists in database or create new one
        med_id = self._med_name.currentData()
        medication_name = med_name_text
        
        if not med_id:
            # New medication - save to database
            db = SessionLocal()
            try:
                dosage_text = self._dosage.text().strip()
                
                new_med = MedicationORM(
                    name=med_name_text,
                    dosage=dosage_text,
                    unit=None
                )
                db.add(new_med)
                db.commit()
                medication_name = new_med.name
                self._load_medications()  # Refresh the combo box
            except Exception as e:
                db.rollback()
                QMessageBox.warning(self, "Попередження", f"Не вдалося зберегти нові ліки: {str(e)}")
            finally:
                db.close()
        
        # Collect times
        times = []
        for time_edit in self._time_inputs:
            time_str = time_edit.time().toString("HH:mm")
            times.append(time_str)
        
        data = {
            "medication_name": medication_name,
            "medication_form": self._med_form.currentText(),
            "dosage": self._dosage.text().strip(),
            "frequency_per_day": self._frequency.value(),
            "specific_times": times,
            "duration_days": self._duration.value(),
            "start_date": self._start_date.date().toPyDate(),
            "take_with_food": self._with_food.isChecked(),
            "take_before_food": self._before_food.isChecked(),
            "take_after_food": self._after_food.isChecked(),
            "special_instructions": self._instructions.toPlainText() or None,
            "prescribed_for": self._prescribed_for.toPlainText() or None,
        }
        
        self._view_model.create_prescription(data)
    
    def _view_prescription(self, prescription_id: int):
        """Show prescription details dialog."""
        prescription = self._view_model.get_prescription(prescription_id)
        if not prescription:
            QMessageBox.warning(self, "Помилка", "Призначення не знайдено")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Призначення #{prescription.prescription_number}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header info
        header = QLabel(f"<h2>💊 {prescription.medication_name}</h2>")
        layout.addWidget(header)
        
        # Details form
        details = QTextEdit()
        details.setReadOnly(True)
        details.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #fafaff, stop:1 #f5f7ff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 12px;
                padding: 14px;
                font-size: 13px;
                color: #334155;
            }
        """)
        
        info_text = f"""
<b>Номер:</b> {prescription.prescription_number}<br>
<b>Дата:</b> {prescription.prescription_date.strftime('%d.%m.%Y') if prescription.prescription_date else '—'}<br>
<b>Статус:</b> {prescription.status}<br><br>

<b>Форма:</b> {prescription.medication_form or '—'}<br>
<b>Дозування:</b> {prescription.dosage}<br>
<b>Частота:</b> {prescription.frequency_per_day} разів на день<br>
<b>Тривалість:</b> {prescription.duration_days or '—'} днів<br>
<b>Початок:</b> {prescription.start_date.strftime('%d.%m.%Y') if prescription.start_date else '—'}<br>
<b>Кінець:</b> {prescription.end_date.strftime('%d.%m.%Y') if prescription.end_date else '—'}<br><br>

<b>Показання:</b> {prescription.prescribed_for or '—'}<br>
<b>Інструкції:</b> {prescription.special_instructions or '—'}<br><br>

<b>Пацієнт повідомлений:</b> {'Так' if prescription.patient_notified else 'Ні'}<br>
<b>Прийнято пацієнтом:</b> {'Так' if prescription.notification_accepted else 'Ні' if prescription.notification_accepted is not None else 'Очікує'}
        """
        details.setHtml(info_text)
        layout.addWidget(details)
        
        # Close button
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def _cancel_prescription(self, prescription_id: int):
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Скасувати це призначення? Пацієнт отримає сповіщення.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.cancel_prescription(prescription_id, "Скасовано лікарем")
    
    def set_patient(self, patient_id: int, patient_name: str):
        """Set current patient context."""
        self._view_model.set_selected_patient(patient_id)
        self._patient_label.setText(f"Пацієнт: {patient_name}")
