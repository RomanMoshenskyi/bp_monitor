"""AI Insights ViewModel - for AI-powered BP predictions and DNA profiling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
import logging

from PyQt6.QtCore import pyqtSignal

from app.presentation.view_models.base_view_model import BaseViewModel
from sqlalchemy.orm import Session

from app.application.services.prediction_service import (
    PredictionService, RiskLevel, BPPatternType, CrisisRiskPrediction, DNAProfile, PatternInsight
)
from app.application.dto.prediction_dto import (
    CrisisRiskPredictionDTO, DNAProfileDTO, TimePatternDTO, PatternInsightDTO,
    AIInsightsSummaryDTO
)
from app.domain.entities import UserORM

_logger = logging.getLogger(__name__)


class AIInsightsViewModel(BaseViewModel):
    """
    ViewModel for AI Insights page.
    
    Provides:
    - Crisis risk prediction (48h ahead)
    - DNA profile (BP pattern classification)
    - Pattern insights
    """
    
    # Signals
    prediction_changed = pyqtSignal(object)  # CrisisRiskPredictionDTO
    dna_profile_changed = pyqtSignal(object)  # DNAProfileDTO
    insights_changed = pyqtSignal(list)  # List[PatternInsightDTO]
    summary_changed = pyqtSignal(object)  # AIInsightsSummaryDTO
    
    def __init__(
        self,
        current_user: UserORM,
        db_session: Session
    ):
        super().__init__()
        self._current_user = current_user
        self._prediction_service = PredictionService(db_session)
        
        # Cached data
        self._prediction: Optional[CrisisRiskPrediction] = None
        self._dna_profile: Optional[DNAProfile] = None
        self._insights: List[PatternInsight] = []
    
    def load(self):
        """Load all AI insights data."""
        self.safe_execute(self._load_data, "Failed to load AI insights")
    
    def refresh_prediction(self):
        """Refresh only the risk prediction."""
        self.safe_execute(self._load_prediction, "Failed to refresh prediction")
    
    def refresh_dna_profile(self):
        """Refresh only the DNA profile."""
        self.safe_execute(self._load_dna_profile, "Failed to refresh DNA profile")
    
    def _load_data(self):
        """Internal data loading."""
        _logger.info(f"Loading AI insights for user {self._current_user.id}")
        
        # Load prediction (48h ahead)
        self._load_prediction()
        
        # Load DNA profile
        self._load_dna_profile()
        
        # Load insights
        self._load_insights()
        
        # Generate summary
        self._generate_summary()
    
    def _load_prediction(self):
        """Load crisis risk prediction."""
        try:
            self._prediction = self._prediction_service.predict_crisis_risk(
                self._current_user, hours_ahead=48
            )
            dto = self._convert_prediction_to_dto(self._prediction)
            self.prediction_changed.emit(dto)
            _logger.info(f"Risk prediction: {dto.risk_percentage}% ({dto.risk_level.value})")
        except Exception as e:
            _logger.error(f"Failed to load prediction: {e}")
    
    def _load_dna_profile(self):
        """Load DNA profile."""
        try:
            self._dna_profile = self._prediction_service.generate_dna_profile(
                self._current_user
            )
            dto = self._convert_dna_profile_to_dto(self._dna_profile)
            self.dna_profile_changed.emit(dto)
            _logger.info(f"DNA profile: {dto.pattern_name}")
        except Exception as e:
            _logger.error(f"Failed to load DNA profile: {e}")
    
    def _load_insights(self):
        """Load pattern insights."""
        try:
            self._insights = self._prediction_service.get_pattern_insights(
                self._current_user
            )
            dtos = [self._convert_insight_to_dto(i) for i in self._insights]
            self.insights_changed.emit(dtos)
            _logger.info(f"Loaded {len(dtos)} insights")
        except Exception as e:
            _logger.error(f"Failed to load insights: {e}")
    
    def _generate_summary(self):
        """Generate summary DTO for dashboard."""
        if not self._prediction or not self._dna_profile:
            return
        
        # Convert insights to DTOs
        insight_dtos = [self._convert_insight_to_dto(i) for i in self._insights]
        
        # Take latest 3 insights
        latest_insights = insight_dtos[:3]
        
        summary = AIInsightsSummaryDTO(
            dna_profile_name=self._dna_profile.pattern_name,
            dna_profile_icon=self._get_pattern_icon(self._dna_profile.pattern_type),
            risk_percentage=self._prediction.risk_percentage,
            risk_level=self._get_risk_display(self._prediction.risk_level),
            risk_color=self._get_risk_color(self._prediction.risk_level),
            stability_score=self._dna_profile.stability_score,
            latest_insights=latest_insights,
            has_critical_risk=self._prediction.risk_level == RiskLevel.CRITICAL,
            updated_at=datetime.utcnow()
        )
        
        self.summary_changed.emit(summary)
    
    # ============= DTO Converters =============
    
    def _convert_prediction_to_dto(
        self, prediction: CrisisRiskPrediction
    ) -> CrisisRiskPredictionDTO:
        """Convert prediction to DTO."""
        return CrisisRiskPredictionDTO(
            risk_level=prediction.risk_level,
            risk_percentage=prediction.risk_percentage,
            prediction_hours=prediction.prediction_hours,
            risk_level_display=self._get_risk_display(prediction.risk_level),
            risk_color=self._get_risk_color(prediction.risk_level),
            factors=prediction.factors,
            recommendations=prediction.recommendations,
            generated_at=prediction.generated_at
        )
    
    def _convert_dna_profile_to_dto(
        self, profile: DNAProfile
    ) -> DNAProfileDTO:
        """Convert DNA profile to DTO."""
        # Convert time patterns
        time_patterns = []
        time_data = [
            ("morning", "🌅 Ранок", profile.morning_avg),
            ("afternoon", "️ День", profile.afternoon_avg),
            ("evening", "🌆 Вечір", profile.evening_avg),
            ("night", "🌙 Ніч", profile.night_avg),
        ]
        
        for period, display, avg in time_data:
            trend = "stable"
            if avg and profile.morning_avg:
                diff = avg - profile.morning_avg
                trend = "up" if diff > 5 else "down" if diff < -5 else "stable"
            
            time_patterns.append(TimePatternDTO(
                period=period,
                display_name=display,
                average_systolic=avg,
                average_diastolic=None,  # Could add later
                measurement_count=0,  # Would need actual count
                trend=trend
            ))
        
        # Medication effectiveness display
        med_effect_display = "Невідомо"
        if profile.medication_effectiveness:
            med_effect_display = f"-{profile.medication_effectiveness:.0f}% АТ"
        
        # Stability rating
        if profile.stability_score >= 80:
            stability_rating = "excellent"
        elif profile.stability_score >= 60:
            stability_rating = "good"
        elif profile.stability_score >= 40:
            stability_rating = "fair"
        else:
            stability_rating = "poor"
        
        # Top recommendations (first 3 insights)
        top_recommendations = profile.insights[:3] if profile.insights else ["Продовжуйте моніторинг"]
        
        return DNAProfileDTO(
            pattern_type=profile.pattern_type,
            pattern_name=profile.pattern_name,
            pattern_description=profile.pattern_description,
            pattern_icon=self._get_pattern_icon(profile.pattern_type),
            time_patterns=time_patterns,
            weather_correlation=profile.weather_correlation,
            weather_sensitivity=profile.weather_sensitivity,
            weather_sensitivity_display=self._get_weather_sensitivity_display(profile.weather_sensitivity),
            medication_effectiveness=profile.medication_effectiveness,
            medication_effectiveness_display=med_effect_display,
            stability_score=profile.stability_score,
            stability_rating=stability_rating,
            variance=profile.variance,
            triggers=profile.triggers,
            insights=profile.insights,
            top_recommendations=top_recommendations,
            generated_at=profile.generated_at,
            data_days=profile.data_days,
            is_insufficient_data=profile.data_days < 10
        )
    
    def _convert_insight_to_dto(
        self, insight: PatternInsight
    ) -> PatternInsightDTO:
        """Convert pattern insight to DTO."""
        trend_icons = {
            "up": "📈",
            "down": "📉",
            "stable": "➡️"
        }
        
        colors = {
            "up": "#22c55e",      # green
            "down": "#ef4444",    # red
            "stable": "#3b82f6"   # blue
        }
        
        return PatternInsightDTO(
            title=insight.title,
            value=insight.value,
            trend=insight.trend,
            trend_icon=trend_icons.get(insight.trend, "➡️"),
            description=insight.description,
            color=colors.get(insight.trend, "#6b7280")
        )
    
    # ============= Helper methods =============
    
    def _get_risk_display(self, level: RiskLevel) -> str:
        """Get Ukrainian display name for risk level."""
        names = {
            RiskLevel.LOW: "Низький ризик",
            RiskLevel.MEDIUM: "Середній ризик",
            RiskLevel.HIGH: "Високий ризик",
            RiskLevel.CRITICAL: "🔴 КРИТИЧНИЙ РИЗИК"
        }
        return names.get(level, "Невідомо")
    
    def _get_risk_color(self, level: RiskLevel) -> str:
        """Get color for risk level."""
        colors = {
            RiskLevel.LOW: "#22c55e",      # green
            RiskLevel.MEDIUM: "#f59e0b",   # yellow
            RiskLevel.HIGH: "#ef4444",     # red
            RiskLevel.CRITICAL: "#dc2626"  # dark red
        }
        return colors.get(level, "#6b7280")
    
    def _get_pattern_icon(self, pattern_type: BPPatternType) -> str:
        """Get emoji icon for pattern type."""
        icons = {
            BPPatternType.MORNING_HYPERTENSIVE: "🌅",
            BPPatternType.WEATHER_REACTIVE: "🌦",
            BPPatternType.STRESS_DEPENDENT: "😰",
            BPPatternType.MEDICATION_DEPENDENT: "💊",
            BPPatternType.EVENING_SPIKER: "🌆",
            BPPatternType.WEEKEND_WARRIOR: "📅",
            BPPatternType.STABLE: "✅",
            BPPatternType.UNPREDICTABLE: "❓"
        }
        return icons.get(pattern_type, "🩺")
    
    def _get_weather_sensitivity_display(self, sensitivity: str) -> str:
        """Get Ukrainian display for weather sensitivity."""
        names = {
            "висока": "🌦 Дуже чутливий до погоди",
            "середня": "🌤 Помірно чутливий",
            "низька": "️ Малочутливий",
            "відсутня": "❌ Не залежить від погоди",
            "невідомо": "❓ Недостатньо даних"
        }
        return names.get(sensitivity, sensitivity)
    
    # ============= Public properties =============
    
    @property
    def current_prediction(self) -> Optional[CrisisRiskPrediction]:
        """Get current prediction."""
        return self._prediction
    
    @property
    def current_dna_profile(self) -> Optional[DNAProfile]:
        """Get current DNA profile."""
        return self._dna_profile
    
    @property
    def user_name(self) -> str:
        """Get current user name."""
        return self._current_user.full_name
