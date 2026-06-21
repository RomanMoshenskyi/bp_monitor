"""Admin pages - comprehensive admin panel functionality."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QLineEdit, QDateEdit, QSpinBox, QTabWidget,
    QScrollArea, QGridLayout, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QTextEdit, QCheckBox, QSizePolicy
)

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from app.domain.entities import (
    UserORM, MeasurementORM, MedicationORM, PrescriptionORM,
    MedicationIntakeORM, AuditLogEntryORM, DoctorReportORM,
    WeatherSnapshotORM
)
from app.infrastructure.orm.base import SessionLocal


class MedicationDialog(QDialog):
    """Dialog for adding/editing medications."""
    
    def __init__(self, parent=None, medication=None):
        super().__init__(parent)
        self._medication = medication
        self.setWindowTitle("Редагувати ліки" if medication else "Додати ліки")
        self.setMinimumWidth(400)
        self._setup_ui()
        
        if medication:
            self._load_medication_data()
    
    def _load_medication_data(self):
        """Load existing medication data into form."""
        if self._medication:
            self._name_edit.setText(self._medication.name)
            self._dosage_edit.setText(self._medication.dosage)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        form = QFormLayout()
        form.setVerticalSpacing(12)
        
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Назва препарату")
        form.addRow("Назва:", self._name_edit)
        
        self._dosage_edit = QLineEdit()
        self._dosage_edit.setPlaceholderText("наприклад, 500 mg або 1 таблетка")
        form.addRow("Дозування:", self._dosage_edit)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        save_btn = QPushButton("Зберегти")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save)
        buttons.addWidget(save_btn)
        
        layout.addLayout(buttons)
    
    def _save(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть назву ліків")
            return
        
        dosage = self._dosage_edit.text().strip()
        if not dosage:
            QMessageBox.warning(self, "Помилка", "Введіть дозування")
            return
        
        db = SessionLocal()
        try:
            if self._medication:
                # Update existing medication - need to merge into new session
                med = db.query(MedicationORM).filter(MedicationORM.id == self._medication.id).first()
                if med:
                    med.name = name
                    med.dosage = dosage
                    db.commit()
            else:
                # Create new medication
                med = MedicationORM(
                    name=name,
                    dosage=dosage,
                    unit=None
                )
                db.add(med)
                db.commit()
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Помилка", f"Не вдалося зберегти ліки: {str(e)}")
        finally:
            db.close()


class GlassCard(QFrame):
    """Glass-style stat card."""
    
    def __init__(self, title: str, value: str, subtitle: str = "", accent_color: str = "#6366f1"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 16px;
                border-left: 4px solid {accent_color};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #94a3b8; font-size: 11.5px; font-weight: 600; letter-spacing: 0.3px;")
        layout.addWidget(title_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(f"color: {accent_color}; font-size: 28px; font-weight: 800; letter-spacing: -0.5px;")
        layout.addWidget(value_lbl)
        
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
            layout.addWidget(sub_lbl)
        
        self._value_label = value_lbl
    
    def set_value(self, value: str):
        self._value_label.setText(value)


class AdminDashboardPage(QWidget):
    """Admin dashboard with system statistics."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(" Системна статистика")
        header.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        layout.addWidget(header)
        
        # Stats grid
        stats = QGridLayout()
        stats.setHorizontalSpacing(12)
        stats.setVerticalSpacing(12)
        
        self._total_users = GlassCard("Користувачі", "—", "Всього в системі", "#6366f1")
        self._total_patients = GlassCard("Пацієнти", "—", "З моніторингом АТ", "#22c55e")
        self._total_doctors = GlassCard("Лікарі", "—", "Активні спеціалісти", "#3b82f6")
        self._total_measurements = GlassCard("Вимірювання", "—", "Загальна кількість", "#f59e0b")
        self._today_measurements = GlassCard("Сьогодні", "—", "Нових замірів", "#8b5cf6")
        self._total_medications = GlassCard("Ліки", "—", "В системі", "#ec4899")
        
        stats.addWidget(self._total_users, 0, 0)
        stats.addWidget(self._total_patients, 0, 1)
        stats.addWidget(self._total_doctors, 0, 2)
        stats.addWidget(self._total_measurements, 1, 0)
        stats.addWidget(self._today_measurements, 1, 1)
        stats.addWidget(self._total_medications, 1, 2)
        
        layout.addLayout(stats)
        
        # Recent activity section
        activity_header = QLabel("🕐 Остання активність")
        activity_header.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px; margin-top: 20px;")
        layout.addWidget(activity_header)
        
        self._activity_table = QTableWidget(0, 4)
        self._activity_table.setHorizontalHeaderLabels(["Час", "Користувач", "Дія", "Деталі"])
        self._activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._activity_table.horizontalHeader().setMinimumSectionSize(80)
        self._activity_table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
        """)
        self._activity_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._activity_table)
        
        layout.addStretch()
    
    def refresh(self):
        db = SessionLocal()
        try:
            # User stats
            total_users = db.query(UserORM).count()
            total_patients = db.query(UserORM).filter(UserORM.role == "patient").count()
            total_doctors = db.query(UserORM).filter(UserORM.role == "doctor").count()
            
            self._total_users.set_value(str(total_users))
            self._total_patients.set_value(str(total_patients))
            self._total_doctors.set_value(str(total_doctors))
            
            # Measurement stats
            total_measurements = db.query(MeasurementORM).count()
            today = datetime.utcnow().date()
            today_measurements = db.query(MeasurementORM).filter(
                func.date(MeasurementORM.measured_at) == today
            ).count()
            
            self._total_measurements.set_value(str(total_measurements))
            self._today_measurements.set_value(str(today_measurements))
            
            # Medications
            total_medications = db.query(MedicationORM).count()
            self._total_medications.set_value(str(total_medications))
            
            # Recent activity
            recent_logs = db.query(AuditLogEntryORM).order_by(
                desc(AuditLogEntryORM.timestamp)
            ).limit(20).all()
            
            self._activity_table.setRowCount(len(recent_logs))
            for i, log in enumerate(recent_logs):
                self._activity_table.setItem(i, 0, QTableWidgetItem(
                    log.timestamp.strftime("%d.%m %H:%M") if log.timestamp else "—"
                ))
                self._activity_table.setItem(i, 1, QTableWidgetItem(
                    log.user.username if log.user else "—"
                ))
                self._activity_table.setItem(i, 2, QTableWidgetItem(log.action))
                self._activity_table.setItem(i, 3, QTableWidgetItem(
                    log.details or ""
                ))
            
        finally:
            db.close()


class AdminAuditLogPage(QWidget):
    """Audit log viewer for admin."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Header with filters
        header = QHBoxLayout()
        
        title = QLabel(" Журнал аудиту")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        
        header.addStretch()
        
        # Filters
        self._user_filter = QLineEdit()
        self._user_filter.setPlaceholderText(" Користувач...")
        self._user_filter.setMinimumWidth(150)
        self._user_filter.setMaximumWidth(200)
        header.addWidget(self._user_filter)
        
        self._action_filter = QComboBox()
        self._action_filter.addItems(["Всі дії", "login", "logout", "measurement_created", 
                                       "measurement_deleted", "user_created", "prescription_created"])
        self._action_filter.setMinimumWidth(140)
        self._action_filter.setMaximumWidth(180)
        header.addWidget(self._action_filter)
        
        refresh_btn = QPushButton("↻ Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setMinimumWidth(110)
        refresh_btn.setMaximumWidth(130)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Table
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels([
            "ID", "Час", "Користувач", "Роль", "Дія", "Деталі"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setMinimumSectionSize(80)
        self._table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
        """)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._table)
        
        # Export button
        export_btn = QPushButton(" Експорт журналу")
        export_btn.setObjectName("secondaryButton")
        export_btn.clicked.connect(self._export_logs)
        layout.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignRight)
    
    def refresh(self):
        db = SessionLocal()
        try:
            query = db.query(AuditLogEntryORM).order_by(desc(AuditLogEntryORM.timestamp))
            
            # Apply filters
            user_filter = self._user_filter.text().strip()
            if user_filter:
                query = query.join(UserORM).filter(UserORM.username.ilike(f"%{user_filter}%"))
            
            action_filter = self._action_filter.currentText()
            if action_filter != "Всі дії":
                query = query.filter(AuditLogEntryORM.action == action_filter)
            
            logs = query.limit(100).all()
            
            self._table.setRowCount(len(logs))
            for i, log in enumerate(logs):
                self._table.setItem(i, 0, QTableWidgetItem(str(log.id)))
                self._table.setItem(i, 1, QTableWidgetItem(
                    log.timestamp.strftime("%d.%m.%Y %H:%M:%S") if log.timestamp else "—"
                ))
                self._table.setItem(i, 2, QTableWidgetItem(
                    log.user.username if log.user else "—"
                ))
                self._table.setItem(i, 3, QTableWidgetItem(
                    log.user.role if log.user else "—"
                ))
                self._table.setItem(i, 4, QTableWidgetItem(log.action))
                self._table.setItem(i, 5, QTableWidgetItem(log.details or ""))
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити журнал аудиту: {str(e)}")
            self._table.setRowCount(0)
        finally:
            db.close()
    
    def _build_log_query(self, db: Session):
        query = db.query(AuditLogEntryORM).order_by(desc(AuditLogEntryORM.timestamp))

        user_filter = self._user_filter.text().strip()
        if user_filter:
            query = query.join(UserORM).filter(UserORM.username.ilike(f"%{user_filter}%"))

        action_filter = self._action_filter.currentText()
        if action_filter != "Всі дії":
            query = query.filter(AuditLogEntryORM.action == action_filter)

        return query

    def _export_logs(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Експорт журналу", "audit_log.csv", "CSV (*.csv)"
        )
        if not path:
            return

        db = SessionLocal()
        try:
            import csv

            logs = self._build_log_query(db).all()
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Час", "Користувач", "Роль", "Дія", "Деталі"])
                for log in logs:
                    writer.writerow([
                        log.id,
                        log.timestamp.strftime("%d.%m.%Y %H:%M:%S") if log.timestamp else "",
                        log.user.username if log.user else "",
                        log.user.role if log.user else "",
                        log.action,
                        log.details or "",
                    ])

            QMessageBox.information(
                self, "Готово", f"Журнал експортовано ({len(logs)} записів) до {path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося експортувати журнал: {str(e)}")
        finally:
            db.close()


class AdminMedicationsPage(QWidget):
    """Admin page for managing all medications in the system."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(" Ліки в системі")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        
        header.addStretch()
        
        self._search = QLineEdit()
        self._search.setPlaceholderText(" Пошук за назвою...")
        self._search.setMinimumWidth(180)
        self._search.setMaximumWidth(250)
        self._search.textChanged.connect(self.refresh)
        header.addWidget(self._search)
        
        add_btn = QPushButton("➕ Додати")
        add_btn.setObjectName("primaryButton")
        add_btn.setMinimumWidth(100)
        add_btn.setMaximumWidth(120)
        add_btn.clicked.connect(self._add_medication)
        header.addWidget(add_btn)
        
        import_btn = QPushButton("📥 Імпорт")
        import_btn.setObjectName("secondaryButton")
        import_btn.setMinimumWidth(100)
        import_btn.setMaximumWidth(120)
        import_btn.clicked.connect(self._import_medications)
        header.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Експорт")
        export_btn.setObjectName("secondaryButton")
        export_btn.setMinimumWidth(100)
        export_btn.setMaximumWidth(120)
        export_btn.clicked.connect(self._export_medications)
        header.addWidget(export_btn)
        
        refresh_btn = QPushButton("↻ Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setMinimumWidth(110)
        refresh_btn.setMaximumWidth(130)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Stats
        stats = QHBoxLayout()
        self._total_meds = QLabel("Всього ліків: —")
        self._total_meds.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: 600;")
        stats.addWidget(self._total_meds)
        stats.addStretch()
        layout.addLayout(stats)
        
        # Table
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels([
            "ID", "Назва", "Дозування", "Додано"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setMinimumSectionSize(80)
        self._table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
        """)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._table)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self._edit_btn = QPushButton("✏️ Редагувати")
        self._edit_btn.setObjectName("secondaryButton")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._edit_medication)
        actions_layout.addWidget(self._edit_btn)
        
        self._delete_btn = QPushButton("🗑️ Видалити")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:disabled {
                background: #fca5a5;
                color: #fecaca;
            }
        """)
        self._delete_btn.clicked.connect(self._delete_medication)
        actions_layout.addWidget(self._delete_btn)
        
        layout.addLayout(actions_layout)
        
        # Connect selection change
        self._table.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _on_selection_changed(self):
        """Enable/disable edit/delete buttons based on selection."""
        has_selection = len(self._table.selectedItems()) > 0
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)
    
    def refresh(self):
        db = SessionLocal()
        try:
            query = db.query(MedicationORM)
            
            search = self._search.text().strip()
            if search:
                query = query.filter(MedicationORM.name.ilike(f"%{search}%"))
            
            medications = query.order_by(desc(MedicationORM.created_at)).all()
            
            self._table.setRowCount(len(medications))
            self._total_meds.setText(f"Всього ліків: {len(medications)}")
            
            for i, med in enumerate(medications):
                self._table.setItem(i, 0, QTableWidgetItem(str(med.id)))
                self._table.setItem(i, 1, QTableWidgetItem(med.name))
                self._table.setItem(i, 2, QTableWidgetItem(med.dosage))
                self._table.setItem(i, 3, QTableWidgetItem(
                    med.created_at.strftime("%d.%m.%Y") if med.created_at else "—"
                ))
        finally:
            db.close()
    
    def _add_medication(self):
        """Open dialog to add new medication."""
        dialog = MedicationDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()
    
    def _edit_medication(self):
        """Open dialog to edit selected medication."""
        selected_items = self._table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Помилка", "Оберіть ліки для редагування")
            return
        
        row = selected_items[0].row()
        med_id = self._table.item(row, 0).text()
        
        db = SessionLocal()
        try:
            med = db.query(MedicationORM).filter(MedicationORM.id == int(med_id)).first()
            if med:
                dialog = MedicationDialog(self, medication=med)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.refresh()
        finally:
            db.close()
    
    def _delete_medication(self):
        """Delete selected medication."""
        selected_items = self._table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Помилка", "Оберіть ліки для видалення")
            return
        
        row = selected_items[0].row()
        med_id = self._table.item(row, 0).text()
        med_name = self._table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Підтвердження",
            f"Ви дійсно хочете видалити ліки '{med_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            try:
                med = db.query(MedicationORM).filter(MedicationORM.id == int(med_id)).first()
                if med:
                    db.delete(med)
                    db.commit()
                    self.refresh()
            except Exception as e:
                db.rollback()
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити ліки: {str(e)}")
            finally:
                db.close()
    
    def _import_medications(self):
        """Import medications from CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Імпорт ліків", "", "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not path:
            return
        
        db = SessionLocal()
        try:
            if path.endswith('.csv'):
                import csv
                with open(path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        med = MedicationORM(
                            name=row.get('name', ''),
                            dosage=row.get('dosage', ''),
                            unit=None
                        )
                        db.add(med)
            elif path.endswith('.json'):
                import json
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        med = MedicationORM(
                            name=item.get('name', ''),
                            dosage=item.get('dosage', ''),
                            unit=None
                        )
                        db.add(med)
            
            db.commit()
            QMessageBox.information(self, "Успіх", "Ліки успішно імпортовано")
            self.refresh()
        except Exception as e:
            db.rollback()
            QMessageBox.critical(self, "Помилка", f"Не вдалося імпортувати ліки: {str(e)}")
        finally:
            db.close()
    
    def _export_medications(self):
        """Export medications to CSV file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Експорт ліків", "medications.csv", "CSV Files (*.csv);;JSON Files (*.json)"
        )
        if not path:
            return
        
        db = SessionLocal()
        try:
            medications = db.query(MedicationORM).all()
            
            if path.endswith('.csv'):
                import csv
                with open(path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=['name', 'dosage'])
                    writer.writeheader()
                    for med in medications:
                        writer.writerow({
                            'name': med.name,
                            'dosage': med.dosage
                        })
            elif path.endswith('.json'):
                import json
                data = [{
                    'name': med.name,
                    'dosage': med.dosage
                } for med in medications]
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Успіх", f"Ліки експортовано до {path}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося експортувати ліки: {str(e)}")
        finally:
            db.close()


class AdminPrescriptionsPage(QWidget):
    """Admin page for viewing all prescriptions."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(" Рецепти та призначення")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        
        header.addStretch()
        
        self._status_filter = QComboBox()
        self._status_filter.addItems(["Всі статуси", "active", "completed", "cancelled", "expired"])
        self._status_filter.currentTextChanged.connect(self.refresh)
        header.addWidget(self._status_filter)
        
        refresh_btn = QPushButton("↻ Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setFixedWidth(130)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Stats
        stats = QHBoxLayout()
        self._active_count = QLabel("Активних: —")
        self._active_count.setStyleSheet("color: #10b981; font-weight: 700; font-size: 13px;")
        stats.addWidget(self._active_count)
        stats.addSpacing(20)
        self._completed_count = QLabel("Завершених: —")
        self._completed_count.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 13px;")
        stats.addWidget(self._completed_count)
        stats.addStretch()
        layout.addLayout(stats)
        
        # Table
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels([
            "ID", "Лікар", "Пацієнт", "Ліки", "Дозування", "Початок", "Кінець", "Статус"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setMinimumSectionSize(80)
        self._table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
        """)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._table)
    
    def refresh(self):
        db = SessionLocal()
        try:
            query = db.query(PrescriptionORM)
            
            status_filter = self._status_filter.currentText()
            if status_filter != "Всі статуси":
                query = query.filter(PrescriptionORM.status == status_filter)
            
            prescriptions = query.order_by(desc(PrescriptionORM.created_at)).all()
            
            # Count stats
            active = db.query(PrescriptionORM).filter(PrescriptionORM.status == "active").count()
            completed = db.query(PrescriptionORM).filter(PrescriptionORM.status == "completed").count()
            self._active_count.setText(f"Активних: {active}")
            self._completed_count.setText(f"Завершених: {completed}")
            
            self._table.setRowCount(len(prescriptions))
            for i, p in enumerate(prescriptions):
                self._table.setItem(i, 0, QTableWidgetItem(str(p.id)))
                self._table.setItem(i, 1, QTableWidgetItem(
                    p.doctor.full_name if p.doctor else "—"
                ))
                self._table.setItem(i, 2, QTableWidgetItem(
                    p.patient.full_name if p.patient else "—"
                ))
                self._table.setItem(i, 3, QTableWidgetItem(p.medication_name or "—"))
                self._table.setItem(i, 4, QTableWidgetItem(p.dosage or "—"))
                self._table.setItem(i, 5, QTableWidgetItem(
                    p.start_date.strftime("%d.%m.%Y") if p.start_date else "—"
                ))
                self._table.setItem(i, 6, QTableWidgetItem(
                    p.end_date.strftime("%d.%m.%Y") if p.end_date else "—"
                ))
                
                status_item = QTableWidgetItem(p.status)
                if p.status == "active":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif p.status == "cancelled":
                    status_item.setForeground(Qt.GlobalColor.red)
                self._table.setItem(i, 7, status_item)
        finally:
            db.close()


class AdminMeasurementsPage(QWidget):
    """Admin page for viewing all measurements in the system."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(" Вимірювання АТ")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        header.addWidget(title)
        
        header.addStretch()
        
        self._patient_filter = QLineEdit()
        self._patient_filter.setPlaceholderText(" Пацієнт...")
        self._patient_filter.setMinimumWidth(150)
        self._patient_filter.setMaximumWidth(200)
        header.addWidget(self._patient_filter)
        
        refresh_btn = QPushButton("↻ Оновити")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setMinimumWidth(110)
        refresh_btn.setMaximumWidth(130)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Stats
        stats = QHBoxLayout()
        self._total_label = QLabel("Всього вимірювань: —")
        self._total_label.setStyleSheet("font-size: 13px; color: #94a3b8; font-weight: 600;")
        stats.addWidget(self._total_label)
        stats.addStretch()
        layout.addLayout(stats)
        
        # Table
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels([
            "ID", "Пацієнт", "Дата", "Систола", "Діастола", "Пульс", "Атм. тиск", "Примітки"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setMinimumSectionSize(80)
        self._table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
        """)
        self._table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._table)
    
    def refresh(self):
        db = SessionLocal()
        try:
            query = db.query(MeasurementORM).join(UserORM)
            
            patient_filter = self._patient_filter.text().strip()
            if patient_filter:
                query = query.filter(UserORM.full_name.ilike(f"%{patient_filter}%"))
            
            measurements = query.order_by(desc(MeasurementORM.measured_at)).limit(100).all()
            
            total = db.query(MeasurementORM).count()
            self._total_label.setText(f"Всього вимірювань: {total} (показано {len(measurements)})")
            
            self._table.setRowCount(len(measurements))
            for i, m in enumerate(measurements):
                self._table.setItem(i, 0, QTableWidgetItem(str(m.id)))
                self._table.setItem(i, 1, QTableWidgetItem(
                    m.user.full_name if m.user else "—"
                ))
                self._table.setItem(i, 2, QTableWidgetItem(
                    m.measured_at.strftime("%d.%m.%Y %H:%M") if m.measured_at else "—"
                ))
                
                sys_item = QTableWidgetItem(str(m.systolic))
                if m.systolic > 140:
                    sys_item.setBackground(Qt.GlobalColor.yellow)
                self._table.setItem(i, 3, sys_item)
                
                self._table.setItem(i, 4, QTableWidgetItem(str(m.diastolic)))
                self._table.setItem(i, 5, QTableWidgetItem(str(m.pulse) if m.pulse else "—"))
                
                weather = ""
                if m.weather_snapshot:
                    weather = f"{m.weather_snapshot.pressure_mmhg} мм"
                self._table.setItem(i, 6, QTableWidgetItem(weather))
                
                self._table.setItem(i, 7, QTableWidgetItem(m.notes or ""))
        finally:
            db.close()
