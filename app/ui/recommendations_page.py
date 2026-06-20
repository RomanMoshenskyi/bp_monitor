"""Recommendations Page - for viewing health recommendations."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox, QTextEdit, QComboBox,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont

from app.presentation.view_models import RecommendationsViewModel


class RecommendationsPage(QWidget):
    """Health recommendations page."""
    
    def __init__(self, view_model: RecommendationsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        self._view_model.load_recommendations()
    
    def _setup_ui(self):
        """Setup page UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        
        title_layout = QVBoxLayout()
        title = QLabel("Рекомендації")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;")
        title_layout.addWidget(title)
        
        self._subtitle_label = QLabel("Завантаження...")
        self._subtitle_label.setStyleSheet("color: #94a3b8; font-weight: 500;")
        title_layout.addWidget(self._subtitle_label)
        
        header.addLayout(title_layout)
        header.addStretch()
        
        # Filter
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("Всі рекомендації", "all")
        self._filter_combo.addItem("Непрочитані", "unread")
        self._filter_combo.addItem("Низька важливість", "low")
        self._filter_combo.addItem("Середня важливість", "medium")
        self._filter_combo.addItem("Висока важливість", "high")
        self._filter_combo.addItem("Критична", "critical")
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self._filter_combo)
        
        # Refresh button
        self._refresh_btn = QPushButton("🔄")
        self._refresh_btn.setToolTip("Оновити")
        self._refresh_btn.clicked.connect(self._on_refresh)
        header.addWidget(self._refresh_btn)
        
        layout.addLayout(header)
        
        # Recommendations list
        self._list_widget = QListWidget()
        self._list_widget.setSpacing(10)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list_widget)
        
        # Loading label
        self._loading_label = QLabel("Завантаження...")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._loading_label)
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.recommendations_changed.connect(self._on_recommendations_changed)
        self._view_model.unread_count_changed.connect(self._on_unread_count_changed)
        self._view_model.error_occurred.connect(self._on_error)
        self._view_model.loading_changed.connect(self._on_loading_changed)
    
    def _on_recommendations_changed(self, recommendations):
        """Update list with recommendations."""
        self._list_widget.clear()
        
        for rec in recommendations:
            item = QListWidgetItem()
            
            # Create widget for item
            widget = RecommendationItemWidget(rec, self._view_model)
            
            item.setSizeHint(widget.sizeHint())
            self._list_widget.addItem(item)
            self._list_widget.setItemWidget(item, widget)
        
        if not recommendations:
            self._list_widget.addItem("Немає рекомендацій")
        
        self._update_subtitle(len(recommendations))
    
    def _on_unread_count_changed(self, count: int):
        """Update subtitle with unread count."""
        if count > 0:
            self._subtitle_label.setText(f"{count} непрочитаних")
            self._subtitle_label.setStyleSheet("color: #f59e0b; font-weight: 700;")
        else:
            self._subtitle_label.setText("Всі рекомендації переглянуто")
            self._subtitle_label.setStyleSheet("color: #10b981; font-weight: 600;")
    
    def _update_subtitle(self, total_count: int):
        """Update subtitle with total count."""
        if total_count == 0:
            self._subtitle_label.setText("Немає рекомендацій")
            self._subtitle_label.setStyleSheet("color: #94a3b8; font-weight: 500;")
    
    def _on_loading_changed(self, is_loading: bool):
        """Update loading state."""
        self._loading_label.setVisible(is_loading)
        self._refresh_btn.setEnabled(not is_loading)
    
    def _on_error(self, message: str):
        """Show error message."""
        QMessageBox.critical(self, "Помилка", message)
    
    def _on_item_clicked(self, item: QListWidgetItem):
        """Handle item click."""
        widget = self._list_widget.itemWidget(item)
        if widget:
            widget.toggle_expanded()
    
    def _on_filter_changed(self, index: int):
        """Handle filter change."""
        filter_value = self._filter_combo.currentData()
        include_read = filter_value != "unread"
        self._view_model.load_recommendations(include_read=include_read)
    
    def _on_refresh(self):
        """Refresh recommendations."""
        self._view_model.load_recommendations()


class RecommendationItemWidget(QFrame):
    """Widget for single recommendation item."""
    
    def __init__(self, recommendation, view_model: RecommendationsViewModel, parent=None):
        super().__init__(parent)
        self._rec = recommendation
        self._view_model = view_model
        self._expanded = False
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup widget UI."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setLineWidth(1)
        
        # Color coding based on severity
        severity_colors = {
            "low": "#ecfdf5",      # Emerald tint
            "medium": "#fffbeb",    # Amber tint
            "high": "#fff1f2",      # Rose tint
            "critical": "#ffe4e6",  # Deeper rose
        }
        bg_color = severity_colors.get(self._rec.severity, "#ffffff")
        self.setStyleSheet(f"background-color: {bg_color}; border-radius: 12px; border: 1px solid rgba(0,0,0,0.04);")
        
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(5)
        
        # Header row
        header = QHBoxLayout()
        
        # Severity badge
        severity_display = {
            "low": "🟢 Низька",
            "medium": "🟡 Середня",
            "high": "🟠 Висока",
            "critical": "🔴 Критична",
        }
        severity_label = QLabel(severity_display.get(self._rec.severity, self._rec.severity))
        severity_label.setStyleSheet("font-weight: 700; font-size: 12px;")
        header.addWidget(severity_label)
        
        # Category
        if self._rec.category:
            category_label = QLabel(f"[{self._rec.category}]")
            category_label.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 11px;")
            header.addWidget(category_label)
        
        header.addStretch()
        
        # Date
        if self._rec.created_at:
            date_text = self._rec.created_at.strftime("%d.%m.%Y %H:%M")
            date_label = QLabel(date_text)
            date_label.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
            header.addWidget(date_label)
        
        self._layout.addLayout(header)
        
        # Message preview (collapsed)
        self._message_preview = QLabel(self._rec.message[:100] + "..." if len(self._rec.message) > 100 else self._rec.message)
        self._message_preview.setWordWrap(True)
        self._layout.addWidget(self._message_preview)
        
        # Full message (expanded, initially hidden)
        self._message_full = QTextEdit()
        self._message_full.setPlainText(self._rec.message)
        self._message_full.setReadOnly(True)
        self._message_full.setMaximumHeight(100)
        self._message_full.setVisible(False)
        self._layout.addWidget(self._message_full)
        
        # Actions row
        actions = QHBoxLayout()
        actions.addStretch()
        
        # Mark as read button
        if not self._rec.is_read:
            read_btn = QPushButton(" Прочитано")
            read_btn.clicked.connect(self._on_mark_read)
            actions.addWidget(read_btn)
        
        # Acknowledge button
        if not self._rec.is_acknowledged:
            ack_btn = QPushButton(" Зрозуміло")
            ack_btn.clicked.connect(self._on_acknowledge)
            actions.addWidget(ack_btn)
        
        self._layout.addLayout(actions)
        
        # Status indicators
        if self._rec.is_read or self._rec.is_acknowledged:
            status_text = []
            if self._rec.is_acknowledged:
                status_text.append(" Підтверджено")
            elif self._rec.is_read:
                status_text.append(" Прочитано")
            
            status_label = QLabel(" | ".join(status_text))
            status_label.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600;")
            self._layout.addWidget(status_label)
    
    def toggle_expanded(self):
        """Toggle expanded state."""
        self._expanded = not self._expanded
        self._message_preview.setVisible(not self._expanded)
        self._message_full.setVisible(self._expanded)
    
    def _on_mark_read(self):
        """Mark recommendation as read."""
        self._view_model.mark_as_read(self._rec.id)
    
    def _on_acknowledge(self):
        """Acknowledge recommendation."""
        reply = QMessageBox.question(
            self, "Підтвердження",
            "Ви розумієте та приймаєте цю рекомендацію?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._view_model.acknowledge(self._rec.id)
