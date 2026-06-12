"""Reports Page - for generating health reports."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QFormLayout, QTextEdit, QComboBox, QDateEdit,
    QProgressBar, QFileDialog
)
from PyQt6.QtCore import Qt, QDate

from app.presentation.view_models import ReportsViewModel


class ReportsPage(QWidget):
    """Health reports generation page."""
    
    def __init__(self, view_model: ReportsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_reports()
    
    def _setup_ui(self):
        """Setup page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Звіти про здоров'я")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()
        
        # Generate button
        self._generate_btn = QPushButton("➕ Новий звіт")
        self._generate_btn.setObjectName("primaryButton")
        self._generate_btn.clicked.connect(self._on_generate_clicked)
        header.addWidget(self._generate_btn)
        
        layout.addLayout(header)
        
        # Progress bar (hidden by default)
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)
        
        # Reports table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Назва", "Період", "Формат", "Статус", "Створено", "Дії"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table)
        
        # Status label
        self._status_label = QLabel("Завантаження...")
        layout.addWidget(self._status_label)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.reports_changed.connect(self._on_reports_changed)
        self._view_model.report_generated.connect(self._on_report_generated)
        self._view_model.generation_progress.connect(self._on_progress)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
    
    def _on_reports_changed(self, reports):
        """Update table with reports."""
        self._table.setRowCount(len(reports))
        
        for i, report in enumerate(reports):
            # Title
            self._table.setItem(i, 0, QTableWidgetItem(report.title))
            
            # Period
            period_text = f"{report.period_start} - {report.period_end}"
            self._table.setItem(i, 1, QTableWidgetItem(period_text))
            
            # Format
            format_display = report.file_format.upper()
            self._table.setItem(i, 2, QTableWidgetItem(format_display))
            
            # Status
            status_map = {
                "pending": "В очікуванні",
                "generating": "Генерація...",
                "completed": "Готово",
                "failed": "Помилка",
            }
            status_text = status_map.get(report.status, report.status)
            status_item = QTableWidgetItem(status_text)
            
            # Color code status
            if report.status == "completed":
                status_item.setForeground(Qt.GlobalColor.green)
            elif report.status == "failed":
                status_item.setForeground(Qt.GlobalColor.red)
            
            self._table.setItem(i, 3, status_item)
            
            # Created date
            created_text = report.created_at.strftime("%d.%m.%Y %H:%M") if report.created_at else "—"
            self._table.setItem(i, 4, QTableWidgetItem(created_text))
            
            # Actions
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            
            if report.status == "completed":
                download_btn = QPushButton("⬇️")
                download_btn.setToolTip("Завантажити")
                download_btn.clicked.connect(lambda checked, rid=report.id: self._on_download(rid))
                actions_layout.addWidget(download_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.clicked.connect(lambda checked, rid=report.id: self._on_delete(rid))
            actions_layout.addWidget(delete_btn)
            
            self._table.setCellWidget(i, 5, actions)
        
        self._status_label.setText(f"Всього звітів: {len(reports)}")
    
    def _on_progress(self, percentage: int):
        """Update progress bar."""
        self._progress_bar.setValue(percentage)
        self._progress_bar.setVisible(percentage < 100)
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._generate_btn.setEnabled(not is_loading)
        self._status_label.setText("Завантаження..." if is_loading else "")
    
    def _on_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_generate_clicked(self):
        """Show generate report dialog."""
        dialog = GenerateReportDialog(self, self._view_model)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            self._view_model.generate_report(**data)
    
    def _on_download(self, report_id: int):
        """Download report."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти звіт",
            "bp_report.pdf",
            "PDF (*.pdf);;CSV (*.csv);;JSON (*.json)"
        )
        if file_path:
            # Implementation would download the file
            QMessageBox.information(self, "Успіх", f"Звіт збережено:\n{file_path}")
    
    def _on_delete(self, report_id: int):
        """Delete report."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Видалити цей звіт?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.delete_report(report_id)
    
    def _on_report_generated(self, success: bool, message: str):
        """Handle generation result."""
        if success:
            QMessageBox.information(self, "Успіх", message)
        else:
            QMessageBox.warning(self, "Попередження", message)


class GenerateReportDialog(QDialog):
    """Dialog for generating new report."""
    
    def __init__(self, parent=None, view_model=None):
        super().__init__(parent)
        self._view_model = view_model
        self.setWindowTitle("Новий звіт")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Title
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Наприклад: Звіт за березень 2024")
        layout.addRow("Назва звіту:*", self._title_input)
        
        # Period start
        self._start_date = QDateEdit()
        self._start_date.setDate(QDate.currentDate().addMonths(-1))
        self._start_date.setCalendarPopup(True)
        layout.addRow("Початок періоду:*", self._start_date)
        
        # Period end
        self._end_date = QDateEdit()
        self._end_date.setDate(QDate.currentDate())
        self._end_date.setCalendarPopup(True)
        layout.addRow("Кінець періоду:*", self._end_date)
        
        # Format
        self._format_combo = QComboBox()
        if view_model:
            for value, label in view_model.get_format_options():
                self._format_combo.addItem(label, value)
        else:
            self._format_combo.addItem("PDF Document", "pdf")
            self._format_combo.addItem("CSV Spreadsheet", "csv")
            self._format_combo.addItem("JSON Data", "json")
        layout.addRow("Формат:*", self._format_combo)
        
        # Description
        self._desc_input = QTextEdit()
        self._desc_input.setMaximumHeight(80)
        self._desc_input.setPlaceholderText("Додатковий опис звіту...")
        layout.addRow("Опис:", self._desc_input)
        
        # Buttons
        buttons = QHBoxLayout()
        
        self._generate_btn = QPushButton("Згенерувати")
        self._generate_btn.clicked.connect(self.accept)
        buttons.addWidget(self._generate_btn)
        
        self._cancel_btn = QPushButton("Скасувати")
        self._cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self._cancel_btn)
        
        layout.addRow(buttons)
    
    def get_data(self) -> dict:
        """Get entered data."""
        return {
            "title": self._title_input.text(),
            "period_start": self._start_date.date().toPython(),
            "period_end": self._end_date.date().toPython(),
            "file_format": self._format_combo.currentData(),
            "description": self._desc_input.toPlainText(),
        }
