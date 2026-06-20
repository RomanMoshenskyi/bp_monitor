"""Prediction DTOs for AI insights and DNA profiling."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum


class RiskLevel(Enum):
    """Risk levels for BP crisis prediction."""
    LOW = "low"        # < 30%
    MEDIUM = "medium"  # 30-60%
    HIGH = "high"      # 60-85%
    CRITICAL = "critical"  # > 85%


class BPPatternType(Enum):
    """Blood pressure pattern types (DNA Profile)."""
    MORNING_HYPERTENSIVE = "morning_hypertensive"
    WEATHER_REACTIVE = "weather_reactive"
    STRESS_DEPENDENT = "stress_dependent"
    MEDICATION_DEPENDENT = "medication_dependent"
    EVENING_SPIKER = "evening_spiker"
    WEEKEND_WARRIOR = "weekend_warrior"
    STABLE = "stable"
    UNPREDICTABLE = "unpredictable"


@dataclass
class CrisisRiskPredictionDTO:
    """Crisis risk prediction result."""
    risk_level: RiskLevel
    risk_percentage: int  # 0-100
    prediction_hours: int  # hours ahead (24, 48, 72)
    risk_level_display: str  # Ukrainian display name
    risk_color: str  # hex color for UI
    factors: List[str]  # reasons for risk
    recommendations: List[str]  # what to do
    generated_at: datetime
    
    @property
    def is_critical(self) -> bool:
        """Check if risk is critical."""
        return self.risk_level == RiskLevel.CRITICAL
    
    @property
    def is_high(self) -> bool:
        """Check if risk is high or above."""
        return self.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)


@dataclass
class TimePatternDTO:
    """Time-based BP pattern."""
    period: str  # morning, afternoon, evening, night
    display_name: str  # Ukrainian name
    average_systolic: Optional[float]
    average_diastolic: Optional[float]
    measurement_count: int
    trend: str  # up, down, stable vs other periods


@dataclass
class DNAProfileDTO:
    """User's blood pressure DNA profile."""
    pattern_type: BPPatternType
    pattern_name: str  # Ukrainian name
    pattern_description: str
    pattern_icon: str  # emoji icon
    
    # Time-based stats
    time_patterns: List[TimePatternDTO]
    
    # Weather correlation
    weather_correlation: Optional[float]  # -1 to 1
    weather_sensitivity: str  # high/medium/low/none
    weather_sensitivity_display: str  # Ukrainian
    
    # Medication effectiveness
    medication_effectiveness: Optional[float]  # % reduction
    medication_effectiveness_display: str
    
    # Stability
    stability_score: int  # 0-100
    stability_rating: str  # excellent/good/fair/poor
    variance: float  # standard deviation
    
    # Insights
    triggers: List[str]  # what causes spikes
    insights: List[str]  # personalized insights
    top_recommendations: List[str]  # top 3 recommendations
    
    generated_at: datetime
    data_days: int  # how many days of data analyzed
    is_insufficient_data: bool


@dataclass
class PatternInsightDTO:
    """Single pattern insight for dashboard."""
    title: str
    value: str
    trend: str  # up/down/stable
    trend_icon: str  # arrow icon
    description: str
    color: str  # hex color


@dataclass
class AIInsightsSummaryDTO:
    """Summary of all AI insights for quick dashboard view."""
    dna_profile_name: str
    dna_profile_icon: str
    risk_percentage: int
    risk_level: str
    risk_color: str
    stability_score: int
    latest_insights: List[PatternInsightDTO]
    has_critical_risk: bool
    updated_at: datetime
