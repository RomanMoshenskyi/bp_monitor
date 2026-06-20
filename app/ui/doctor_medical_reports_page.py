"""Doctor Medical Reports Page - Professional medical report creation."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QTextEdit, QComboBox, QDateEdit, QSpinBox,
    QGroupBox, QScrollArea, QFrame, QGridLayout, QCheckBox, QFileDialog,
    QSplitter, QTabWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QIcon

from app.presentation.view_models import DoctorReportsViewModel
from app.auth import AuthService, ROLE_DOCTOR


class DoctorMedicalReportsPage(QWidget):
    """
    Medical reports page for doctors.
    
    Features:
    - Create professional medical reports with full clinical documentation
    - View history of created reports (private to doctor)
    - Sign reports electronically
    - Generate and download HTML/PDF reports
    """
    
    def __init__(self, view_model: DoctorReportsViewModel, auth_service: AuthService = None):
        super().__init__()
        self._view_model = view_model
        self._auth = auth_service or AuthService()
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_reports()
    
    def _setup_ui(self):
        """Setup the page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self._create_header()
        layout.addLayout(header)
        
        # Main content - tabs
        self._tabs = QTabWidget()
        self._tabs.setObjectName("modernTabs")
        
        # Tab 1: Create Report
        self._create_tab = self._create_report_tab()
        self._tabs.addTab(self._create_tab, " Новий звіт")
        
        # Tab 2: Report History
        self._history_tab = self._create_history_tab()
        self._tabs.addTab(self._history_tab, " Історія звітів")
        
        layout.addWidget(self._tabs)
        
        # Status bar
        self._status_label = QLabel("Готово")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)
    
    def _create_header(self) -> QHBoxLayout:
        """Create page header."""
        header = QHBoxLayout()
        
        title = QLabel(" Медичні звіти")
        title.setObjectName("pageTitle")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        header.addWidget(title)
        
        header.addStretch()
        
        # Patient selector (for context)
        self._patient_label = QLabel("Пацієнт: не обрано")
        self._patient_label.setObjectName("patientLabel")
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
    
    def _create_report_tab(self) -> QWidget:
        """Create the new report form tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Scroll area for long form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(20)
        
        # Form sections - using simplified version
        form_layout.addWidget(self._create_basic_info_section())
        form_layout.addWidget(self._create_medical_data_section())
        form_layout.addLayout(self._create_report_actions())
        
        form_layout.addStretch()
        scroll.setWidget(form_container)
        layout.addWidget(scroll)
        
        return tab
    
    def _create_basic_info_section(self) -> QGroupBox:
        """Create basic report information section."""
        group = QGroupBox(" Основна інформація")
        group.setObjectName("formSection")
        layout = QGridLayout(group)
        layout.setSpacing(12)
        
        # Report date
        self._report_date = QDateEdit()
        self._report_date.setDate(QDate.currentDate())
        self._report_date.setCalendarPopup(True)
        self._report_date.setDisplayFormat("dd.MM.yyyy")
        layout.addWidget(QLabel("Дата звіту:*"), 0, 0)
        layout.addWidget(self._report_date, 0, 1)
        
        return group
    
    def _create_medical_data_section(self) -> QGroupBox:
        """Create medical data section."""
        group = QGroupBox(" Медичні дані")
        group.setObjectName("formSection")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Chief complaint
        self._chief_complaint = QTextEdit()
        self._chief_complaint.setPlaceholderText("Головні скарги пацієнта...")
        self._chief_complaint.setMaximumHeight(80)
        layout.addWidget(QLabel("Головні скарги:"))
        layout.addWidget(self._chief_complaint)
        
        # Diagnosis
        self._final_diagnosis = QTextEdit()
        self._final_diagnosis.setPlaceholderText("Заключний діагноз...*")
        self._final_diagnosis.setMaximumHeight(60)
        layout.addWidget(QLabel("Діагноз:*"))
        layout.addWidget(self._final_diagnosis)
        
        # Treatment/Prescriptions
        self._prescriptions = QTextEdit()
        self._prescriptions.setPlaceholderText("Призначені ліки та лікування...")
        layout.addWidget(QLabel("Призначення:"))
        layout.addWidget(self._prescriptions)
        
        # Conclusion
        self._conclusion = QTextEdit()
        self._conclusion.setPlaceholderText("Заключення лікаря...*")
        self._conclusion.setMaximumHeight(80)
        layout.addWidget(QLabel("Заключення:*"))
        layout.addWidget(self._conclusion)
        
        return group
    
    def _create_report_actions(self) -> QHBoxLayout:
        """Create action buttons."""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        
        layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton(" Очистити")
        clear_btn.setObjectName("secondaryButton")
        clear_btn.clicked.connect(self._clear_form)
        layout.addWidget(clear_btn)
        
        # Create and sign button
        sign_btn = QPushButton("✍️ Створити та підписати")
        sign_btn.setObjectName("primaryButton")
        sign_btn.clicked.connect(self._create_and_sign_report)
        layout.addWidget(sign_btn)
        
        return layout
    
    def _create_history_tab(self) -> QWidget:
        """Create the report history tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        
        # Info label
        info = QLabel(" Звіти видно тільки вам як лікарю, який їх створив")
        info.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 13px;
                font-weight: 500;
                padding: 12px 18px;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #eff6ff, stop:1 #dbeafe);
                border-radius: 12px;
                border-left: 4px solid #3b82f6;
            }
        """)
        layout.addWidget(info)
        
        # Action bar
        self._action_bar = QFrame()
        self._action_bar.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fafc,stop:1 #f1f5f9); border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        action_layout = QHBoxLayout(self._action_bar)
        action_layout.setContentsMargins(12, 8, 12, 8)
        action_layout.setSpacing(8)
        
        self._selected_label = QLabel("Оберіть звіт для дій")
        self._selected_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        action_layout.addWidget(self._selected_label)
        action_layout.addStretch()
        
        self._view_btn = QPushButton("👁 Переглянути")
        self._view_btn.setEnabled(False)
        self._view_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#6366f1;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#4f46e5;}")
        self._view_btn.clicked.connect(self._on_view_selected)
        action_layout.addWidget(self._view_btn)
        
        self._download_btn = QPushButton("⬇ Завантажити")
        self._download_btn.setEnabled(False)
        self._download_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#06b6d4;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#0891b2;}")
        self._download_btn.clicked.connect(self._on_download_selected)
        action_layout.addWidget(self._download_btn)
        
        self._sign_btn = QPushButton("✍ Підписати")
        self._sign_btn.setEnabled(False)
        self._sign_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#10b981;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#059669;}")
        self._sign_btn.clicked.connect(self._on_sign_selected)
        action_layout.addWidget(self._sign_btn)
        
        self._delete_btn = QPushButton("✕ Видалити")
        self._delete_btn.setEnabled(False)
        self._delete_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#f43f5e;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#e11d48;}")
        self._delete_btn.clicked.connect(self._on_delete_selected)
        action_layout.addWidget(self._delete_btn)
        
        layout.addWidget(self._action_bar)
        
        # Reports table
        self._reports_table = QTableWidget()
        self._reports_table.setColumnCount(5)
        self._reports_table.setHorizontalHeaderLabels([
            "№ Звіту", "Дата", "Діагноз", "Підпис", "Створено"
        ])
        self._reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._reports_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._reports_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._reports_table.setAlternatingRowColors(True)
        self._reports_table.verticalHeader().setVisible(False)
        self._reports_table.verticalHeader().setDefaultSectionSize(40)
        self._reports_table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self._reports_table)
        
        return tab
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.reports_changed.connect(self._on_reports_changed)
        self._view_model.report_created.connect(self._on_report_created)
        self._view_model.report_signed.connect(self._on_report_signed)
        self._view_model.report_generated.connect(self._on_report_generated)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
    
    def _on_reports_changed(self, reports):
        """Update reports table."""
        self._reports_table.setRowCount(len(reports))
        
        for i, report in enumerate(reports):
            self._reports_table.setItem(i, 0, QTableWidgetItem(report.report_number))
            
            date_text = report.report_date.strftime("%d.%m.%Y") if report.report_date else "—"
            self._reports_table.setItem(i, 1, QTableWidgetItem(date_text))
            
            diagnosis = report.final_diagnosis or report.preliminary_diagnosis or "—"
            if len(diagnosis) > 50:
                diagnosis = diagnosis[:50] + "..."
            self._reports_table.setItem(i, 2, QTableWidgetItem(diagnosis))
            
            signed_text = " Підписано" if report.is_signed else "✗ Не підписано"
            signed_item = QTableWidgetItem(signed_text)
            if report.is_signed:
                signed_item.setForeground(QColor("#38a169"))
            else:
                signed_item.setForeground(QColor("#e53e3e"))
            self._reports_table.setItem(i, 3, signed_item)
            
            created_text = report.created_at.strftime("%d.%m.%Y") if report.created_at else "—"
            self._reports_table.setItem(i, 4, QTableWidgetItem(created_text))
            
            # Store report ID in item for selection handling
            self._reports_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, report.id)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        selected_items = self._reports_table.selectedItems()
        if not selected_items:
            self._selected_label.setText("Оберіть звіт для дій")
            self._view_btn.setEnabled(False)
            self._download_btn.setEnabled(False)
            self._sign_btn.setEnabled(False)
            self._delete_btn.setEnabled(False)
            self._selected_report_id = None
            return
        
        # Get report ID from first column
        self._selected_report_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        report = self._view_model.get_report(self._selected_report_id)
        
        if report:
            self._selected_label.setText(f"Обрано: Звіт #{report.report_number}")
            self._view_btn.setEnabled(True)
            self._download_btn.setEnabled(True)
            self._sign_btn.setEnabled(not report.is_signed)
            self._delete_btn.setEnabled(True)
    
    def _on_view_selected(self):
        """View selected report."""
        if self._selected_report_id:
            self._view_report(self._selected_report_id)
    
    def _on_download_selected(self):
        """Download selected report."""
        if self._selected_report_id:
            self._download_report(self._selected_report_id)
    
    def _on_sign_selected(self):
        """Sign selected report."""
        if self._selected_report_id:
            self._sign_report(self._selected_report_id)
    
    def _on_delete_selected(self):
        """Delete selected report."""
        if self._selected_report_id:
            self._delete_report(self._selected_report_id)
    
    def _on_report_created(self, success, message):
        if success:
            QMessageBox.information(self, "Успіх", message)
            self._clear_form()
            self._tabs.setCurrentIndex(1)
        else:
            QMessageBox.warning(self, "Помилка", message)
    
    def _on_report_signed(self, success, message):
        if success:
            QMessageBox.information(self, "Успіх", message)
        else:
            QMessageBox.warning(self, "Помилка", message)
    
    def _on_report_generated(self, success, message, file_path):
        if success:
            QMessageBox.information(self, "Успіх", message)
        else:
            QMessageBox.warning(self, "Помилка", message)
    
    def _on_error(self, message):
        QMessageBox.critical(self, "Помилка", message)
        self._status_label.setText(f" {message}")
    
    def _on_loading_changed(self, is_loading):
        if is_loading:
            self._status_label.setText("⏳ Завантаження...")
        else:
            self._status_label.setText(" Готово")
    
    def _collect_form_data(self) -> dict:
        return {
            "report_date": self._report_date.date().toPyDate(),
            "chief_complaint": self._chief_complaint.toPlainText() or None,
            "final_diagnosis": self._final_diagnosis.toPlainText() or None,
            "prescriptions": self._prescriptions.toPlainText() or None,
            "doctor_conclusion": self._conclusion.toPlainText() or None,
        }
    
    def _clear_form(self):
        self._chief_complaint.clear()
        self._final_diagnosis.clear()
        self._prescriptions.clear()
        self._conclusion.clear()
    
    def _create_and_sign_report(self):
        if not self._final_diagnosis.toPlainText().strip():
            QMessageBox.warning(self, "Помилка", "Діагноз є обов'язковим")
            return
        
        if not self._conclusion.toPlainText().strip():
            QMessageBox.warning(self, "Помилка", "Заключення є обов'язковим")
            return
        
        data = self._collect_form_data()
        self._view_model.create_report(data)
    
    def _view_report(self, report_id: int):
        """Show report details dialog."""
        report = self._view_model.get_report(report_id)
        if not report:
            QMessageBox.warning(self, "Помилка", "Звіт не знайдено")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Медичний звіт #{report.report_number}")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"<h2> Медичний звіт</h2>")
        layout.addWidget(header)
        
        # Report info
        info = QLabel(f"""
        <b>Номер:</b> {report.report_number}<br>
        <b>Дата:</b> {report.report_date.strftime('%d.%m.%Y') if report.report_date else '—'}<br>
        <b>Підписано:</b> {'Так' if report.is_signed else 'Ні'}<br>
        <b>Лікар:</b> {report.doctor_signature_name or '—'}
        """)
        layout.addWidget(info)
        
        # Details
        details = QTextEdit()
        details.setReadOnly(True)
        details.setStyleSheet("""
            QTextEdit {
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        
        details_text = f"""
<b>Діагноз:</b><br>{report.final_diagnosis or report.preliminary_diagnosis or '—'}<br><br>

<b>Заключення:</b><br>{report.doctor_conclusion or '—'}<br><br>

<b>Призначення:</b><br>{report.prescriptions or '—'}<br><br>

<b>Скарги:</b><br>{report.chief_complaint or '—'}
        """
        details.setHtml(details_text)
        layout.addWidget(details)
        
        # Actions
        actions = QHBoxLayout()
        
        if not report.is_signed:
            sign_btn = QPushButton("✍️ Підписати")
            sign_btn.clicked.connect(lambda: self._sign_and_close(report_id, dialog))
            actions.addWidget(sign_btn)
        
        download_btn = QPushButton("⬇️ Завантажити HTML")
        download_btn.clicked.connect(lambda: self._download_and_stay(report_id))
        actions.addWidget(download_btn)
        
        actions.addStretch()
        
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(dialog.accept)
        actions.addWidget(close_btn)
        
        layout.addLayout(actions)
        
        dialog.exec()
    
    def _sign_and_close(self, report_id: int, dialog):
        """Sign report and close dialog."""
        self._sign_report(report_id)
        dialog.accept()
    
    def _download_and_stay(self, report_id: int):
        """Download report without closing dialog."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт", f"medical_report_{report_id}.html", "HTML (*.html)"
        )
        if file_path:
            self._view_model.generate_html_report(report_id, file_path)
    
    def _download_report(self, report_id: int):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти звіт", f"medical_report_{report_id}.html", "HTML (*.html)"
        )
        if file_path:
            self._view_model.generate_html_report(report_id, file_path)
    
    def _sign_report(self, report_id: int):
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Підписати цей медичний звіт?\n\nПісля підписання звіт не можна буде редагувати.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.sign_report(report_id)
    
    def _delete_report(self, report_id: int):
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Видалити цей звіт? Цю дію не можна скасувати.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_report(report_id)
    
    def set_patient(self, patient_id: int, patient_name: str):
        """Set current patient context."""
        self._view_model.set_selected_patient(patient_id)
        self._patient_label.setText(f"Пацієнт: {patient_name}")
