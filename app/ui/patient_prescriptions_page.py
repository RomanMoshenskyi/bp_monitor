"""Patient Prescriptions Page - View prescriptions, track intake, calendar."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QDialog,
    QFrame, QGridLayout, QScrollArea, QGroupBox, QTextEdit,
    QComboBox, QSpinBox, QListWidget, QListWidgetItem, QStackedWidget,
    QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen

from app.presentation.view_models import PrescriptionsViewModel
from app.application.dto import PrescriptionIntakeDTO
from datetime import datetime, timedelta


class MedicationCalendar(QWidget):
    """
    Traditional monthly calendar for medication adherence.
    Shows days in a grid with clear visual indicators.
    """
    
    # Colors for different adherence levels
    COLORS = {
        "empty": "#f8fafc",      # No data/empty
        "none": "#e2e8f0",       # No medications
        "poor": "#ffe4e6",       # <50% (rose tint)
        "fair": "#fef3c7",       # 50-75% (amber tint)
        "good": "#d1fae5",       # 75-95% (emerald light)
        "perfect": "#6ee7b7",    # >95% (emerald)
        "border": "#e2e8f0",
        "text": "#1e293b",
        "header_bg": "#f1f5f9",
    }
    
    day_clicked = pyqtSignal(dict)  # Emits day data on click
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._current_year = QDate.currentDate().year()
        self._current_month = QDate.currentDate().month()
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with month navigation
        header = QWidget()
        header.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f"stop:0 {self.COLORS['header_bg']}, stop:1 #eef2ff);"
            f"border-radius: 10px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        self._month_label = QLabel()
        self._month_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #0f172a; letter-spacing: -0.2px;")
        self._month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self._month_label)
        
        layout.addWidget(header)
        
        # Days of week header
        days_header = QWidget()
        days_header.setStyleSheet("background: transparent;")
        days_layout = QHBoxLayout(days_header)
        days_layout.setSpacing(4)
        days_layout.setContentsMargins(0, 8, 0, 4)
        
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]
        for day in days:
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 0.3px;")
            days_layout.addWidget(label)
        
        layout.addWidget(days_header)
        
        # Calendar grid
        self._grid = QGridLayout()
        self._grid.setSpacing(4)
        self._grid.setContentsMargins(0, 0, 0, 0)
        
        self._day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = QPushButton()
                btn.setFixedSize(65, 50)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, r=row, c=col: self._on_day_clicked(r, c))
                self._grid.addWidget(btn, row, col)
                self._day_buttons.append((btn, row, col))
        
        layout.addLayout(self._grid)
        layout.addStretch()
        
        self._update_display()
    
    def set_data(self, days_data: list):
        """Set calendar data from list of day entries."""
        self._data = {}
        for day_entry in days_data:
            date_str = day_entry.get("date", "")
            if date_str:
                self._data[date_str] = day_entry
        self._update_display()
    
    def set_month(self, year: int, month: int):
        """Set displayed month."""
        self._current_year = year
        self._current_month = month
        self._update_display()
    
    def _update_display(self):
        """Update calendar display for current month."""
        # Update month label
        months = ["", "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                  "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
        self._month_label.setText(f"{months[self._current_month]} {self._current_year}")
        
        # Get first day of month
        first_day = QDate(self._current_year, self._current_month, 1)
        start_column = first_day.dayOfWeek() - 1  # 0=Monday
        days_in_month = first_day.daysInMonth()
        
        # Clear all buttons
        for btn, row, col in self._day_buttons:
            btn.setText("")
            btn.setStyleSheet(self._get_day_style("empty"))
            btn.setEnabled(False)
            btn.setProperty("day_data", None)
        
        # Fill in days
        day_index = 0
        for day in range(1, days_in_month + 1):
            row = (start_column + day - 1) // 7
            col = (start_column + day - 1) % 7
            
            if row < 6:  # Only 6 rows max
                btn = self._day_buttons[row * 7 + col][0]
                btn.setText(str(day))
                btn.setEnabled(True)
                
                # Get day data
                date_str = f"{self._current_year:04d}-{self._current_month:02d}-{day:02d}"
                day_data = self._data.get(date_str, {"total": 0, "taken": 0, "level": 0})
                
                # Determine color based on adherence
                if day_data["total"] == 0:
                    color_key = "none"
                else:
                    adherence = day_data["taken"] / day_data["total"]
                    if adherence >= 0.95:
                        color_key = "perfect"
                    elif adherence >= 0.75:
                        color_key = "good"
                    elif adherence >= 0.5:
                        color_key = "fair"
                    else:
                        color_key = "poor"
                
                btn.setStyleSheet(self._get_day_style(color_key))
                btn.setProperty("day_data", day_data)
    
    def _get_day_style(self, color_key: str) -> str:
        """Get stylesheet for day button based on adherence level."""
        color = self.COLORS.get(color_key, self.COLORS["empty"])
        border_color = self.COLORS["border"]
        text_color = self.COLORS["text"]
        
        return f"""
            QPushButton {{
                background: {color};
                border: 1.5px solid {border_color};
                border-radius: 10px;
                font-size: 13px;
                font-weight: 700;
                color: {text_color};
            }}
            QPushButton:hover {{
                border: 1.5px solid #94a3b8;
            }}
            QPushButton:disabled {{
                background: {self.COLORS["empty"]};
                border: none;
                color: transparent;
            }}
        """
    
    def _on_day_clicked(self, row: int, col: int):
        """Handle day button click."""
        btn = self._day_buttons[row * 7 + col][0]
        day_data = btn.property("day_data")
        if day_data:
            self._show_day_details(day_data)
            self.day_clicked.emit(day_data)
    
    def _show_day_details(self, day_data: dict):
        """Show details for selected day."""
        date_str = day_data.get("date", "Unknown")
        total = day_data.get("total", 0)
        taken = day_data.get("taken", 0)
        missed = day_data.get("missed", 0)
        skipped = day_data.get("skipped", 0)
        level = day_data.get("level", 0)
        intakes = day_data.get("intakes", [])  # List of intake details with times
        
        if total == 0:
            status_text = " На цей день не було призначень"
        else:
            adherence = taken / total * 100
            if adherence >= 95:
                status_text = f" Відмінно! Прийнято {taken}/{total} ({adherence:.0f}%)"
            elif adherence >= 75:
                status_text = f" Добре! Прийнято {taken}/{total} ({adherence:.0f}%)"
            elif adherence >= 50:
                status_text = f" Задовільно. Прийнято {taken}/{total} ({adherence:.0f}%)"
            else:
                status_text = f" Потрібно покращити. Прийнято {taken}/{total} ({adherence:.0f}%)"
        
        # Build intake details with times
        intake_details = ""
        if intakes:
            intake_details = "<hr><h4> Деталі прийому:</h4><table cellpadding='4' style='border-collapse: collapse;'>"
            for intake in intakes:
                med_name = intake.get("medication_name", "Невідомо")
                dosage = intake.get("dosage", "")
                scheduled = intake.get("scheduled_time", "")
                taken_at = intake.get("taken_at", "")
                status = intake.get("status", "")
                
                # Format times
                scheduled_time = ""
                if scheduled:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(scheduled.replace('Z', '+00:00'))
                        scheduled_time = dt.strftime("%H:%M")
                    except:
                        scheduled_time = scheduled
                
                taken_time = ""
                if taken_at:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(taken_at.replace('Z', '+00:00'))
                        taken_time = dt.strftime("%H:%M")
                    except:
                        taken_time = taken_at
                
                status_emoji = ""
                if status == "taken":
                    status_emoji = "✓"
                elif status == "missed":
                    status_emoji = "✗"
                elif status == "skipped":
                    status_emoji = "⊘"
                
                intake_details += f"""
                <tr style='border-bottom: 1px solid #e2e8f0;'>
                    <td style='padding: 6px;'>{med_name} {dosage}</td>
                    <td style='padding: 6px;'>Заплановано: {scheduled_time}</td>
                    <td style='padding: 6px;'>Прийнято: <b>{taken_time if taken_time else '—'}</b></td>
                    <td style='padding: 6px;'>{status_emoji}</td>
                </tr>
                """
            intake_details += "</table>"
        
        msg_text = f"""
        <h3> {date_str}</h3>
        <p style="font-size:14px;">{status_text}</p>
        <hr>
        <table cellpadding="4">
        <tr><td> Прийнято:</td><td><b>{taken}</b></td></tr>
        <tr><td> Пропущено:</td><td><b>{missed}</b></td></tr>
        <tr><td> Скасовано:</td><td><b>{skipped}</b></td></tr>
        </table>
        {intake_details}
        <tr><td><b>Всього:</b></td><td><b>{total}</b></td></tr>
        </table>
        """
        
        QMessageBox.information(self, f"Статистика за день", msg_text)


class PatientPrescriptionsPage(QWidget):
    """
    Prescriptions page for patients.
    
    Features:
    - View active prescriptions from doctors
    - Track medication intake
    - GitHub-style adherence calendar
    - Missed medication reminders
    """
    
    def __init__(self, view_model: PrescriptionsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        
        # Initial data load
        self._view_model.load_patient_prescriptions()
        self._view_model.load_pending_intakes()
        self._view_model.load_calendar_data()
        self._view_model.load_adherence_stats()
    
    def _setup_ui(self):
        """Setup the page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = self._create_header()
        layout.addLayout(header)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(24)
        
        # Notifications section (if there are missed intakes)
        self._notifications_section = self._create_notifications_section()
        content_layout.addWidget(self._notifications_section)
        
        # Upcoming intakes
        upcoming = self._create_upcoming_intakes_section()
        content_layout.addWidget(upcoming)
        
        # Calendar section
        calendar = self._create_calendar_section()
        content_layout.addWidget(calendar)
        
        # Stats section
        stats = self._create_stats_section()
        content_layout.addWidget(stats)
        
        # Prescriptions list
        prescriptions = self._create_prescriptions_section()
        content_layout.addWidget(prescriptions)
        
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
    
    def _create_header(self) -> QHBoxLayout:
        """Create page header."""
        header = QHBoxLayout()
        
        title = QLabel(" Мої ліки")
        title.setObjectName("pageTitle")
        title_font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        title.setFont(title_font)
        header.addWidget(title)
        
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Оновити")
        refresh_btn.clicked.connect(self._refresh_data)
        header.addWidget(refresh_btn)
        
        return header
    
    def _create_notifications_section(self) -> QWidget:
        """Create missed medication notifications."""
        self._notifications_widget = QWidget()
        self._notifications_widget.setVisible(False)
        self._notifications_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #fff1f2, stop:1 #ffe4e6);
                border: 1.5px solid rgba(244,63,94,0.25);
                border-radius: 14px;
                padding: 18px;
            }
        """)
        
        layout = QVBoxLayout(self._notifications_widget)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("⚠ Нагадування про пропущені прийоми")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #e11d48;")
        layout.addWidget(header)
        
        # Missed intakes list
        self._missed_list = QListWidget()
        self._missed_list.setMaximumHeight(150)
        layout.addWidget(self._missed_list)
        
        return self._notifications_widget
    
    def _create_upcoming_intakes_section(self) -> QWidget:
        """Create upcoming intakes section."""
        group = QGroupBox("⏰ Найближчі прийоми")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(6,182,212,0.18);
                border-radius: 16px;
                padding: 18px;
                margin-top: 14px;
                color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #0891b2;
            }
        """)
        
        layout = QVBoxLayout(group)
        
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
        
        self._take_btn = QPushButton("✓ Прийняв")
        self._take_btn.setEnabled(False)
        self._take_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#10b981;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#059669;}")
        self._take_btn.clicked.connect(self._on_take_clicked)
        action_layout.addWidget(self._take_btn)
        
        self._skip_btn = QPushButton("✗ Пропустив")
        self._skip_btn.setEnabled(False)
        self._skip_btn.setStyleSheet("QPushButton:disabled{background:#cbd5e1;color:#94a3b8;}QPushButton{background:#f43f5e;color:white;border:none;border-radius:6px;padding:8px 16px;font-weight:600;}QPushButton:hover{background:#e11d48;}")
        self._skip_btn.clicked.connect(self._on_skip_clicked)
        action_layout.addWidget(self._skip_btn)
        
        layout.addWidget(self._action_bar)
        
        self._upcoming_table = QTableWidget()
        self._upcoming_table.setColumnCount(3)
        self._upcoming_table.setHorizontalHeaderLabels([
            "Ліки", "Заплановано", "Час до"
        ])
        self._upcoming_table.setMinimumHeight(200)
        self._upcoming_table.setMaximumHeight(350)
        self._upcoming_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._upcoming_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._upcoming_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._upcoming_table.setAlternatingRowColors(True)
        self._upcoming_table.verticalHeader().setVisible(False)
        self._upcoming_table.verticalHeader().setDefaultSectionSize(40)
        self._upcoming_table.itemSelectionChanged.connect(self._on_upcoming_selection_changed)
        self._upcoming_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._upcoming_table, 1)
        
        return group
    
    def _create_calendar_section(self) -> QWidget:
        """Create adherence calendar section with new traditional calendar."""
        group = QGroupBox(" Календар прийому ліків")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 16px;
                padding: 18px;
                margin-top: 14px;
                color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #4f46e5;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Info text
        info_label = QLabel(
            " Клікніть на будь-який день календаря, щоб переглянути детальну статистику прийому ліків.\n"
            "Колір дня показує рівень прихильності:  потрібно покращити   задовільно   добре   відмінно"
        )
        info_label.setStyleSheet("color: #94a3b8; font-size: 11.5px; padding: 4px 0; font-weight: 500;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Simple legend
        legend = QHBoxLayout()
        legend.setSpacing(12)
        
        legend_items = [
            ("#9ae6b4", " Відмінно", ">95%"),
            ("#c6f6d5", " Добре", "75-95%"),
            ("#fefcbf", " Задовільно", "50-75%"),
            ("#fed7d7", " Потрібно покращити", "<50%"),
            ("#e2e8f0", "— Немає даних", "—"),
        ]
        
        for color, label, percent in legend_items:
            item = QWidget()
            item_layout = QHBoxLayout(item)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(4)
            
            color_box = QLabel()
            color_box.setFixedSize(16, 16)
            color_box.setStyleSheet(f"background: {color}; border-radius: 5px; border: 1px solid rgba(203,213,225,0.5);")
            item_layout.addWidget(color_box)
            
            text = QLabel(f"{label}")
            text.setStyleSheet("font-size: 10.5px; color: #64748b; font-weight: 500;")
            item_layout.addWidget(text)
            
            legend.addWidget(item)
        
        legend.addStretch()
        layout.addLayout(legend)
        
        # Calendar widget
        self._calendar = MedicationCalendar()
        layout.addWidget(self._calendar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Month selector
        month_layout = QHBoxLayout()
        self._month_selector = QComboBox()
        months = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень",
                  "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]
        self._month_selector.addItems(months)
        self._month_selector.setCurrentIndex(QDate.currentDate().month() - 1)
        month_layout.addWidget(QLabel(" Місяць:"))
        month_layout.addWidget(self._month_selector)
        
        self._year_selector = QSpinBox()
        self._year_selector.setRange(2020, 2099)
        self._year_selector.setValue(QDate.currentDate().year())
        self._year_selector.setMinimumWidth(80)
        self._year_selector.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        month_layout.addWidget(QLabel("Рік:"))
        month_layout.addWidget(self._year_selector)
        
        update_btn = QPushButton("Оновити календар")
        update_btn.setMinimumWidth(140)
        update_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #06b6d4, stop:1 #0891b2);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 32px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0891b2, stop:1 #0e7490);
            }
        """)
        update_btn.clicked.connect(self._update_calendar)
        month_layout.addWidget(update_btn)
        
        month_layout.addStretch()
        layout.addLayout(month_layout)
        
        return group
    
    def _create_stats_section(self) -> QWidget:
        """Create adherence statistics section."""
        self._stats_widget = QWidget()
        self._stats_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #fafaff, stop:1 #f5f7ff);
                border: 1.5px solid rgba(226,232,240,0.45);
                border-radius: 16px;
                padding: 18px;
            }
        """)
        
        layout = QHBoxLayout(self._stats_widget)
        layout.setSpacing(20)
        
        # Stats cards
        self._adherence_card = self._create_stat_card("Прихильність", "—%", "#38a169")
        self._taken_card = self._create_stat_card("Прийнято", "—", "#3182ce")
        self._missed_card = self._create_stat_card("Пропущено", "—", "#e53e3e")
        
        layout.addWidget(self._adherence_card)
        layout.addWidget(self._taken_card)
        layout.addWidget(self._missed_card)
        layout.addStretch()
        
        return self._stats_widget
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a statistics card."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid {color}18;
                border-radius: 14px;
                padding: 18px;
                min-width: 120px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 11.5px; color: #94a3b8; font-weight: 600; letter-spacing: 0.3px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color}; letter-spacing: -0.5px;")
        layout.addWidget(value_label)
        
        # Store reference to update later
        card._value_label = value_label
        
        return card
    
    def _create_prescriptions_section(self) -> QWidget:
        """Create prescriptions list section."""
        group = QGroupBox(" Активні призначення")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                font-size: 14px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 16px;
                padding: 18px;
                margin-top: 14px;
                color: #0f172a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 10px;
                color: #4f46e5;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        self._prescriptions_table = QTableWidget()
        self._prescriptions_table.setColumnCount(5)
        self._prescriptions_table.setHorizontalHeaderLabels([
            "Ліки", "Дозування", "Частота", "Тривалість", "До кінця"
        ])
        self._prescriptions_table.setMinimumHeight(200)
        self._prescriptions_table.setMaximumHeight(350)
        self._prescriptions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._prescriptions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._prescriptions_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._prescriptions_table.setAlternatingRowColors(True)
        self._prescriptions_table.verticalHeader().setVisible(False)
        self._prescriptions_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._prescriptions_table, 1)
        
        return group
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.prescriptions_changed.connect(self._on_prescriptions_changed)
        self._view_model.intakes_changed.connect(self._on_intakes_changed)
        self._view_model.pending_intakes_changed.connect(self._on_pending_intakes_changed)
        self._view_model.missed_intakes_changed.connect(self._on_missed_intakes_changed)
        self._view_model.calendar_data_changed.connect(self._on_calendar_data_changed)
        self._view_model.adherence_stats_changed.connect(self._on_adherence_stats_changed)
        self._view_model.intake_recorded.connect(self._on_intake_recorded)
        self._view_model.error_occurred.connect(self._on_error)
    
    def _on_prescriptions_changed(self, prescriptions):
        """Update prescriptions table."""
        self._prescriptions_table.setRowCount(len(prescriptions))
        
        for i, rx in enumerate(prescriptions):
            self._prescriptions_table.setItem(i, 0, QTableWidgetItem(rx.medication_name))
            self._prescriptions_table.setItem(i, 1, QTableWidgetItem(rx.dosage))
            
            freq_text = f"{rx.frequency_per_day} разів на день"
            self._prescriptions_table.setItem(i, 2, QTableWidgetItem(freq_text))
            
            duration_text = f"{rx.duration_days} днів" if rx.duration_days else "—"
            self._prescriptions_table.setItem(i, 3, QTableWidgetItem(duration_text))
            
            # Days remaining
            if rx.end_date:
                days_left = (rx.end_date - datetime.now().date()).days
                days_text = f"{max(0, days_left)} днів"
            else:
                days_text = "—"
            self._prescriptions_table.setItem(i, 4, QTableWidgetItem(days_text))
    
    def _on_pending_intakes_changed(self, intakes):
        """Update upcoming intakes table."""
        self._upcoming_table.setRowCount(len(intakes[:10]))  # Show first 10
        
        for i, intake in enumerate(intakes[:10]):
            # Medication name - use medication_name if available, otherwise dosage, or fallback to ID
            med_name = intake.medication_name or intake.dosage or f"Ліки #{intake.id}"
            self._upcoming_table.setItem(i, 0, QTableWidgetItem(med_name))
            
            # Scheduled time
            time_text = intake.scheduled_time.strftime("%d.%m %H:%M") if intake.scheduled_time else "—"
            self._upcoming_table.setItem(i, 1, QTableWidgetItem(time_text))
            
            # Time until
            if intake.scheduled_time:
                minutes = intake.time_until()
                grace_period = intake.is_in_grace_period()
                if minutes is not None:
                    if minutes < 0:
                        # Already passed scheduled time
                        if grace_period:
                            # Within grace period (0-5 hours) - yellow warning
                            time_until_text = f"⚠ {abs(minutes)} хв тому"
                            item = QTableWidgetItem(time_until_text)
                            item.setForeground(QColor("#d69e2e"))  # Yellow for grace period
                        else:
                            # Overdue (>5 hours)
                            time_until_text = f"{abs(minutes)} хв тому"
                            item = QTableWidgetItem(time_until_text)
                            item.setForeground(QColor("#e53e3e"))  # Red for overdue
                    elif minutes < 60:
                        time_until_text = f"через {minutes} хв"
                        item = QTableWidgetItem(time_until_text)
                        item.setForeground(QColor("#dd6b20"))  # Orange for soon
                    else:
                        hours = minutes // 60
                        time_until_text = f"через {hours} год"
                        item = QTableWidgetItem(time_until_text)
                else:
                    item = QTableWidgetItem("—")
            else:
                item = QTableWidgetItem("—")
            
            self._upcoming_table.setItem(i, 2, item)
            
            # Store intake ID in item for selection handling
            self._upcoming_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, intake.id)
    
    def _on_upcoming_selection_changed(self):
        """Handle upcoming table selection change - update button states."""
        selected_items = self._upcoming_table.selectedItems()
        if not selected_items:
            self._take_btn.setEnabled(False)
            self._skip_btn.setEnabled(False)
            self._selected_intake_id = None
            return
        
        # Get intake ID from first column
        self._selected_intake_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self._take_btn.setEnabled(bool(self._selected_intake_id))
        self._skip_btn.setEnabled(bool(self._selected_intake_id))
    
    def _on_take_clicked(self):
        """Handle take button click."""
        if self._selected_intake_id:
            self._record_intake(self._selected_intake_id)
    
    def _on_skip_clicked(self):
        """Handle skip button click."""
        if self._selected_intake_id:
            self._skip_intake(self._selected_intake_id)
    
    def _on_missed_intakes_changed(self, intakes):
        """Show missed intakes notifications."""
        if intakes:
            self._notifications_widget.setVisible(True)
            self._missed_list.clear()
            
            for intake in intakes:
                time_str = intake.scheduled_time.strftime("%d.%m %H:%M") if intake.scheduled_time else "—"
                item_text = f"⚠ Пропущено: Ліки #{intake.id} (було заплановано на {time_str})"
                list_item = QListWidgetItem(item_text)
                self._missed_list.addItem(list_item)
        else:
            self._notifications_widget.setVisible(False)
    
    def _on_calendar_data_changed(self, data):
        """Update calendar with new data."""
        if data and "days" in data:
            self._calendar.set_data(data["days"])
            # Also update month display
            if "year" in data and "month" in data:
                self._calendar.set_month(data["year"], data["month"])
    
    def _on_adherence_stats_changed(self, stats):
        """Update statistics cards."""
        if not stats:
            return
        
        adherence = stats.get("adherence_rate", 0)
        taken = stats.get("taken", 0)
        missed = stats.get("missed", 0)
        self._adherence_card._value_label.setText(f"{adherence}%")
        self._taken_card._value_label.setText(str(taken))
        self._missed_card._value_label.setText(str(missed))
        
        # Update adherence color
        if adherence >= 90:
            color = "#38a169"
        elif adherence >= 75:
            color = "#3182ce"
        elif adherence >= 60:
            color = "#dd6b20"
        else:
            color = "#e53e3e"
        
        self._adherence_card._value_label.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color}; letter-spacing: -0.5px;")
    
    def _on_intake_recorded(self, success, message):
        if success:
            QMessageBox.information(self, "Успіх", message)
            self._view_model.load_pending_intakes()
            self._view_model.load_calendar_data()
        else:
            QMessageBox.warning(self, "Помилка", message)
    
    def _on_error(self, message):
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_intakes_changed(self, intakes):
        pass  # Handled by specific signals
    
    def _record_intake(self, intake_id: int):
        """Record medication intake."""
        self._view_model.record_intake(intake_id)
        # Refresh data after recording
        self._refresh_data()
    
    def _skip_intake(self, intake_id: int):
        """Skip medication intake."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Позначити цей прийом як пропущений?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.skip_intake(intake_id, "Пропущено пацієнтом")
            # Refresh data after skip
            self._refresh_data()
    
    def _update_calendar(self):
        """Update calendar for selected month."""
        year = self._year_selector.value()
        month = self._month_selector.currentIndex() + 1
        self._view_model.load_calendar_data(year, month)
    
    def _refresh_data(self):
        """Refresh all data."""
        self._view_model.load_patient_prescriptions()
        self._view_model.load_pending_intakes()
        self._view_model.load_calendar_data()
        self._view_model.load_adherence_stats()
