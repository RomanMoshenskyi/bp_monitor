"""AI Insights Page - AI-powered BP predictions and DNA profiling."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton, QGridLayout, QScrollArea,
    QSizePolicy, QSpacerItem
)

from app.presentation.view_models import AIInsightsViewModel
from app.application.dto.prediction_dto import (
    CrisisRiskPredictionDTO, DNAProfileDTO, PatternInsightDTO
)


class AIInsightsPage(QWidget):
    """
    AI Insights page with:
    - Crisis risk prediction (48h ahead)
    - DNA profile (BP pattern classification)
    - Pattern insights
    """
    
    def __init__(self, view_model: AIInsightsViewModel):
        super().__init__()
        self._view_model = view_model
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self._view_model.load()
    
    def _setup_ui(self):
        """Setup the page UI."""
        self.setObjectName("AIInsightsPage")
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Main container
        container = QWidget()
        container.setObjectName("insightsContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Risk Prediction Section (Main highlight)
        self._risk_section = self._create_risk_section()
        layout.addWidget(self._risk_section)
        
        # DNA Profile Section
        self._dna_section = self._create_dna_section()
        layout.addWidget(self._dna_section)
        
        # Pattern Insights
        self._insights_section = self._create_insights_section()
        layout.addWidget(self._insights_section)
        
        layout.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll)
    
    def _create_header(self) -> QWidget:
        """Create page header."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title with AI badge
        title_box = QVBoxLayout()
        
        ai_badge = QLabel("AI-POWERED")
        ai_badge.setStyleSheet("""
            QLabel {
                color: #7c3aed;
                font-size: 10.5px;
                font-weight: 800;
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ede9fe, stop:1 #ddd6fe);
                padding: 5px 12px;
                border-radius: 12px;
                letter-spacing: 1.2px;
                border: 1px solid rgba(139,92,246,0.15);
            }
        """)
        title_box.addWidget(ai_badge)
        
        title = QLabel("Розумний аналіз тиску")
        title.setStyleSheet("""
            QLabel {
                font-size: 28px;
                font-weight: 800;
                color: #0f172a;
                letter-spacing: -0.5px;
            }
        """)
        title_box.addWidget(title)
        
        subtitle = QLabel(f"Персональний прогноз для {self._view_model.user_name}")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        title_box.addWidget(subtitle)
        
        layout.addLayout(title_box)
        layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("↻ Оновити аналіз")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fafc, stop:1 #f1f5f9);
                border: 1.5px solid rgba(226,232,240,0.65);
                border-radius: 12px;
                padding: 10px 20px;
                color: #475569;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #eef2ff, stop:1 #e0e7ff);
                border-color: rgba(99,102,241,0.2);
                color: #4f46e5;
            }
        """)
        refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(refresh_btn)
        
        return header
    
    def _create_risk_section(self) -> QFrame:
        """Create risk prediction section."""
        section = QFrame()
        section.setObjectName("riskSection")
        section.setStyleSheet("""
            QFrame#riskSection {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #ffffff, stop:1 #fcfcff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 18px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        
        # Section title
        title = QLabel(" Прогноз ризику на 48 годин")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;")
        layout.addWidget(title)
        
        # Risk display container
        risk_container = QHBoxLayout()
        
        # Risk percentage circle
        self._risk_circle = QFrame()
        self._risk_circle.setFixedSize(140, 140)
        self._risk_circle.setStyleSheet("""
            QFrame {
                background: #f0fdf4;
                border: 4px solid #22c55e;
                border-radius: 70px;
            }
        """)
        
        circle_layout = QVBoxLayout(self._risk_circle)
        circle_layout.setContentsMargins(0, 0, 0, 0)
        circle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._risk_percent_label = QLabel("--")
        self._risk_percent_label.setStyleSheet("""
            font-size: 38px;
            font-weight: 800;
            color: #22c55e;
            letter-spacing: -0.5px;
        """)
        self._risk_percent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle_layout.addWidget(self._risk_percent_label)
        
        risk_label = QLabel("ризик")
        risk_label.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 600; letter-spacing: 0.5px;")
        risk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle_layout.addWidget(risk_label)
        
        risk_container.addWidget(self._risk_circle)
        risk_container.addSpacing(24)
        
        # Risk details
        details = QVBoxLayout()
        details.setSpacing(8)
        
        self._risk_level_label = QLabel("Завантаження...")
        self._risk_level_label.setStyleSheet("""
            font-size: 22px;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.3px;
        """)
        details.addWidget(self._risk_level_label)
        
        self._risk_factors_label = QLabel("")
        self._risk_factors_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        self._risk_factors_label.setWordWrap(True)
        details.addWidget(self._risk_factors_label)
        
        risk_container.addLayout(details, 1)
        layout.addLayout(risk_container)
        
        # Recommendations
        self._recommendations_widget = QWidget()
        rec_layout = QVBoxLayout(self._recommendations_widget)
        rec_layout.setContentsMargins(0, 0, 0, 0)
        rec_layout.setSpacing(8)
        
        rec_title = QLabel("Рекомендації:")
        rec_title.setStyleSheet("font-weight: 700; color: #334155; font-size: 14px;")
        rec_layout.addWidget(rec_title)
        
        self._recommendations_layout = QVBoxLayout()
        self._recommendations_layout.setSpacing(6)
        rec_layout.addLayout(self._recommendations_layout)
        
        layout.addWidget(self._recommendations_widget)
        
        return section
    
    def _create_dna_section(self) -> QFrame:
        """Create DNA profile section."""
        section = QFrame()
        section.setObjectName("dnaSection")
        section.setStyleSheet("""
            QFrame#dnaSection {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ede9fe, stop:0.5 #e0e7ff, stop:1 #ddd6fe);
                border: 1.5px solid rgba(139,92,246,0.12);
                border-radius: 18px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        
        # Header with icon
        header = QHBoxLayout()
        
        self._dna_icon = QLabel("")
        self._dna_icon.setStyleSheet("font-size: 40px;")
        header.addWidget(self._dna_icon)
        
        title_box = QVBoxLayout()
        
        title = QLabel("Ваш ДНК-профіль АТ")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #5b21b6; letter-spacing: -0.3px;")
        title_box.addWidget(title)
        
        self._dna_type_label = QLabel("Аналізуємо дані...")
        self._dna_type_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #6d28d9;
        """)
        title_box.addWidget(self._dna_type_label)
        
        header.addLayout(title_box, 1)
        layout.addLayout(header)
        
        # Description
        self._dna_description = QLabel("")
        self._dna_description.setStyleSheet("""
            color: #7c3aed;
            font-size: 14px;
            line-height: 1.5;
        """)
        self._dna_description.setWordWrap(True)
        layout.addWidget(self._dna_description)
        
        # Stats grid
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(16)
        stats_grid.setVerticalSpacing(12)
        
        # Time patterns
        self._time_stats_labels = {}
        times = [
            ("morning", "Ранок", "6:00-12:00"),
            ("afternoon", "День", "12:00-18:00"),
            ("evening", "Вечір", "18:00-24:00"),
            ("night", "Ніч", "0:00-6:00"),
        ]
        
        for i, (key, name, hours) in enumerate(times):
            card = self._create_time_card(key, name, hours)
            stats_grid.addWidget(card, i // 2, i % 2)
        
        layout.addLayout(stats_grid)
        
        # Additional insights
        self._dna_insights_widget = QWidget()
        insights_layout = QVBoxLayout(self._dna_insights_widget)
        insights_layout.setContentsMargins(0, 8, 0, 0)
        insights_layout.setSpacing(8)
        
        # Weather sensitivity
        self._weather_label = QLabel("")
        self._weather_label.setStyleSheet("color: #5b21b6; font-size: 13px;")
        insights_layout.addWidget(self._weather_label)
        
        # Stability
        self._stability_label = QLabel("")
        self._stability_label.setStyleSheet("color: #5b21b6; font-size: 13px;")
        insights_layout.addWidget(self._stability_label)
        
        layout.addWidget(self._dna_insights_widget)
        
        return section
    
    def _create_time_card(self, key: str, name: str, hours: str) -> QFrame:
        """Create time pattern stat card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.75);
                border: 1px solid rgba(139,92,246,0.08);
                border-radius: 14px;
                padding: 4px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 12px; color: #7c3aed; font-weight: 600;")
        layout.addWidget(name_label)
        
        self._time_stats_labels[key] = QLabel("—")
        self._time_stats_labels[key].setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #5b21b6;
        """)
        layout.addWidget(self._time_stats_labels[key])
        
        hours_label = QLabel(hours)
        hours_label.setStyleSheet("font-size: 10px; color: #8b5cf6;")
        layout.addWidget(hours_label)
        
        return card
    
    def _create_insights_section(self) -> QFrame:
        """Create pattern insights section."""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #fafaff, stop:1 #f5f7ff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 18px;
            }
        """)
        
        layout = QVBoxLayout(section)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        title = QLabel(" Ключові інсайти")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a; letter-spacing: -0.2px;")
        layout.addWidget(title)
        
        # Insights grid
        self._insights_layout = QGridLayout()
        self._insights_layout.setHorizontalSpacing(12)
        self._insights_layout.setVerticalSpacing(12)
        
        layout.addLayout(self._insights_layout)
        
        return section
    
    def _connect_signals(self):
        """Connect ViewModel signals."""
        self._view_model.prediction_changed.connect(self._on_prediction_changed)
        self._view_model.dna_profile_changed.connect(self._on_dna_profile_changed)
        self._view_model.insights_changed.connect(self._on_insights_changed)
    
    def _on_prediction_changed(self, prediction: CrisisRiskPredictionDTO):
        """Update risk prediction UI."""
        # Update percentage
        self._risk_percent_label.setText(f"{prediction.risk_percentage}%")
        
        # Update circle color
        self._risk_circle.setStyleSheet(f"""
            QFrame {{
                background: {prediction.risk_color}20;
                border: 4px solid {prediction.risk_color};
                border-radius: 70px;
            }}
        """)
        self._risk_percent_label.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 800;
            color: {prediction.risk_color};
        """)
        
        # Update level label
        self._risk_level_label.setText(prediction.risk_level_display)
        
        # Update factors
        if prediction.factors:
            factors_text = " " + "\n ".join(prediction.factors)
            self._risk_factors_label.setText(f"Фактори ризику:\n{factors_text}")
        else:
            self._risk_factors_label.setText("Фактори ризику не виявлені")
        
        # Update recommendations
        # Clear old recommendations
        while self._recommendations_layout.count():
            item = self._recommendations_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for rec in prediction.recommendations:
            rec_label = QLabel(f" {rec}")
            rec_label.setStyleSheet("""
                color: #334155;
                font-size: 13px;
                font-weight: 500;
                padding: 6px 0;
            """)
            rec_label.setWordWrap(True)
            self._recommendations_layout.addWidget(rec_label)
        
        # Show/hide section based on critical risk
        if prediction.is_critical:
            self._risk_section.setStyleSheet("""
                QFrame#riskSection {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #fef2f2, stop:1 #fff1f2);
                    border: 2px solid #f43f5e;
                    border-radius: 18px;
                }
            """)
    
    def _on_dna_profile_changed(self, profile: DNAProfileDTO):
        """Update DNA profile UI."""
        # Update icon and name
        self._dna_icon.setText(profile.pattern_icon)
        self._dna_type_label.setText(profile.pattern_name)
        
        # Update description
        self._dna_description.setText(profile.pattern_description)
        
        # Update time stats
        for tp in profile.time_patterns:
            if tp.average_systolic:
                label = self._time_stats_labels.get(tp.period)
                if label:
                    label.setText(f"{tp.average_systolic:.0f} мм")
                    
                    # Color based on value
                    if tp.average_systolic > 140:
                        label.setStyleSheet("font-size: 20px; font-weight: 700; color: #ef4444;")
                    elif tp.average_systolic > 120:
                        label.setStyleSheet("font-size: 20px; font-weight: 700; color: #f59e0b;")
                    else:
                        label.setStyleSheet("font-size: 20px; font-weight: 700; color: #22c55e;")
        
        # Update weather sensitivity
        self._weather_label.setText(f" Погодна чутливість: {profile.weather_sensitivity_display}")
        
        # Update stability
        stability_emoji = "" if profile.stability_score > 70 else "" if profile.stability_score > 40 else ""
        self._stability_label.setText(
            f"{stability_emoji} Стабільність АТ: {profile.stability_score}/100 "
            f"(σ = {profile.variance:.1f})"
        )
        
        # Show warning if insufficient data
        if profile.is_insufficient_data:
            self._dna_section.setStyleSheet("""
                QFrame#dnaSection {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #fefce8, stop:1 #fef9c3);
                    border: 2px dashed #eab308;
                    border-radius: 18px;
                }
            """)
    
    def _on_insights_changed(self, insights: List[PatternInsightDTO]):
        """Update insights UI."""
        # Clear old insights
        while self._insights_layout.count():
            item = self._insights_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new insights (max 4)
        for i, insight in enumerate(insights[:4]):
            card = self._create_insight_card(insight)
            row = i // 2
            col = i % 2
            self._insights_layout.addWidget(card, row, col)
    
    def _create_insight_card(self, insight: PatternInsightDTO) -> QFrame:
        """Create single insight card."""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #ffffff, stop:1 #fafaff);
                border: 1.5px solid rgba(226,232,240,0.55);
                border-radius: 14px;
            }
            QFrame:hover {
                border-color: rgba(99,102,241,0.2);
            }
        """)
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)
        
        # Trend icon
        trend_label = QLabel(insight.trend_icon)
        trend_label.setStyleSheet(f"font-size: 20px; color: {insight.color};")
        layout.addWidget(trend_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        title = QLabel(insight.title)
        title.setStyleSheet("font-weight: 700; color: #1e293b; font-size: 13px;")
        content.addWidget(title)
        
        value = QLabel(insight.value)
        value.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 800;
            color: {insight.color};
        """)
        content.addWidget(value)
        
        desc = QLabel(insight.description)
        desc.setStyleSheet("color: #64748b; font-size: 11px;")
        desc.setWordWrap(True)
        content.addWidget(desc)
        
        layout.addLayout(content, 1)
        
        return card
    
    def _on_refresh(self):
        """Refresh all data."""
        self._view_model.load()
    
    def refresh(self):
        """Public refresh method."""
        self._view_model.load()
