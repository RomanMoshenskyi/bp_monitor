"""Prediction Service - AI-powered blood pressure risk analysis.

Rule-based analytics without external AI APIs:
- Pattern detection from historical data
- Weather correlation analysis
- Risk scoring based on multiple factors
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from enum import Enum
import math

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.domain.entities import UserORM, MeasurementORM, MedicationIntakeORM, PrescriptionORM
from app.infrastructure.orm.base import SessionLocal


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
class CrisisRiskPrediction:
    """Crisis risk prediction result."""
    risk_level: RiskLevel
    risk_percentage: int  # 0-100
    prediction_hours: int  # hours ahead (24, 48, 72)
    factors: List[str]  # reasons for risk
    recommendations: List[str]  # what to do
    generated_at: datetime


@dataclass
class DNAProfile:
    """User's blood pressure DNA profile."""
    pattern_type: BPPatternType
    pattern_name: str  # Ukrainian name
    pattern_description: str
    
    # Time-based stats
    morning_avg: Optional[float]  # 6-12
    afternoon_avg: Optional[float]  # 12-18
    evening_avg: Optional[float]  # 18-24
    night_avg: Optional[float]  # 0-6
    
    # Weather correlation
    weather_correlation: Optional[float]  # -1 to 1
    weather_sensitivity: str  # high/medium/low/none
    
    # Medication effectiveness
    medication_effectiveness: Optional[float]  # % reduction
    
    # Stability
    stability_score: int  # 0-100
    variance: float  # standard deviation
    
    # Insights
    triggers: List[str]  # what causes spikes
    insights: List[str]  # personalized insights
    
    generated_at: datetime
    data_days: int  # how many days of data analyzed


@dataclass
class PatternInsight:
    """Single pattern insight."""
    title: str
    value: str
    trend: str  # up/down/stable
    description: str


class PredictionService:
    """Service for BP predictions and DNA profiling."""
    
    # Risk thresholds
    HIGH_BP_SYSTOLIC = 140
    HIGH_BP_DIASTOLIC = 90
    CRISIS_SYSTOLIC = 180
    CRISIS_DIASTOLIC = 110
    
    def __init__(self, db_session: Session):
        self._db = db_session
    
    def predict_crisis_risk(
        self,
        user: UserORM,
        hours_ahead: int = 48
    ) -> CrisisRiskPrediction:
        """Predict risk of hypertensive crisis in next N hours."""
        factors = []
        recommendations = []
        risk_score = 0
        
        # Get recent data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        measurements = self._db.query(MeasurementORM).filter(
            and_(
                MeasurementORM.user_id == user.id,
                MeasurementORM.measured_at >= start_date,
                MeasurementORM.measured_at <= end_date
            )
        ).order_by(MeasurementORM.measured_at.desc()).all()
        
        # Factor 1: Recent high readings
        recent_high = self._analyze_recent_high_readings(measurements)
        if recent_high:
            risk_score += 25
            factors.append("Недавні високі показники АТ")
            recommendations.append("Виміряйтеся сьогодні о 20:00")
        
        # Factor 2: Missed medications
        missed_meds = self._analyze_missed_medications(user.id)
        if missed_meds > 2:
            risk_score += 20
            factors.append(f"Пропущено {missed_meds} прийомів ліків")
            recommendations.append("Прийміть пропущені ліки за графіком")
        
        # Factor 3: Weather forecast correlation
        weather_risk = self._analyze_weather_risk(user.id, measurements)
        if weather_risk:
            risk_score += 20
            factors.append("Завтра різка зміна атмосферного тиску")
            recommendations.append("Уникайте кави та фізичних навантажень")
        
        # Factor 4: Pattern-based risk
        pattern_risk = self._analyze_pattern_risk(measurements, hours_ahead)
        risk_score += pattern_risk
        if pattern_risk > 15:
            factors.append("За вашим патерном очікується сплеск")
        
        # Factor 5: Days since last measurement
        days_since = self._days_since_last_measurement(measurements)
        if days_since > 2:
            risk_score += 15
            factors.append(f"Не вимірювалися {days_since} днів")
            recommendations.append("Терміново виміряйте АТ")
        
        # Cap at 100
        risk_score = min(100, risk_score)
        
        # Determine risk level
        if risk_score >= 85:
            risk_level = RiskLevel.CRITICAL
            recommendations.insert(0, "⚠️ РИЗИК КРИЗИ! Зверніться до лікаря")
        elif risk_score >= 60:
            risk_level = RiskLevel.HIGH
            recommendations.insert(0, "🔴 Високий ризик - дотримуйтесь рекомендацій")
        elif risk_score >= 30:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        if not recommendations:
            recommendations.append("Продовжуйте моніторинг")
        
        return CrisisRiskPrediction(
            risk_level=risk_level,
            risk_percentage=risk_score,
            prediction_hours=hours_ahead,
            factors=factors,
            recommendations=recommendations,
            generated_at=datetime.utcnow()
        )
    
    def generate_dna_profile(self, user: UserORM) -> DNAProfile:
        """Generate user's BP DNA profile from 90 days of data."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        measurements = self._db.query(MeasurementORM).filter(
            and_(
                MeasurementORM.user_id == user.id,
                MeasurementORM.measured_at >= start_date,
                MeasurementORM.measured_at <= end_date
            )
        ).order_by(MeasurementORM.measured_at.desc()).all()
        
        if len(measurements) < 10:
            return self._create_insufficient_data_profile()
        
        # Time-based analysis
        time_stats = self._analyze_time_patterns(measurements)
        
        # Weather correlation
        weather_corr = self._calculate_weather_correlation(measurements)
        weather_sens = self._classify_weather_sensitivity(weather_corr)
        
        # Pattern classification
        pattern_type = self._classify_pattern(measurements, time_stats, weather_corr)
        pattern_name, pattern_desc = self._get_pattern_info(pattern_type)
        
        # Medication effectiveness
        med_effect = self._calculate_medication_effectiveness(user.id)
        
        # Stability
        variance = self._calculate_variance(measurements)
        stability = max(0, min(100, 100 - int(variance * 2)))
        
        # Insights
        triggers = self._identify_triggers(measurements)
        insights = self._generate_insights(
            pattern_type, time_stats, weather_corr, med_effect, triggers
        )
        
        return DNAProfile(
            pattern_type=pattern_type,
            pattern_name=pattern_name,
            pattern_description=pattern_desc,
            morning_avg=time_stats.get("morning"),
            afternoon_avg=time_stats.get("afternoon"),
            evening_avg=time_stats.get("evening"),
            night_avg=time_stats.get("night"),
            weather_correlation=weather_corr,
            weather_sensitivity=weather_sens,
            medication_effectiveness=med_effect,
            stability_score=stability,
            variance=variance,
            triggers=triggers,
            insights=insights,
            generated_at=datetime.utcnow(),
            data_days=len(measurements)
        )
    
    def get_pattern_insights(self, user: UserORM) -> List[PatternInsight]:
        """Get list of pattern insights for dashboard."""
        profile = self.generate_dna_profile(user)
        insights = []
        
        # Time pattern insight
        if profile.morning_avg and profile.evening_avg:
            diff = profile.morning_avg - profile.evening_avg
            trend = "up" if diff > 5 else "down" if diff < -5 else "stable"
            insights.append(PatternInsight(
                title="Ранковий сплеск",
                value=f"{profile.morning_avg:.0f} мм",
                trend=trend,
                description="Середній АТ уранці (6-12)"
            ))
        
        # Weather insight
        if profile.weather_correlation:
            trend = "up" if profile.weather_correlation > 0.3 else "down" if profile.weather_correlation < -0.3 else "stable"
            insights.append(PatternInsight(
                title="Погодна чутливість",
                value=profile.weather_sensitivity,
                trend=trend,
                description=f"Кореляція з атм. тиском: {profile.weather_correlation:.2f}"
            ))
        
        # Stability insight
        insights.append(PatternInsight(
            title="Стабільність АТ",
            value=f"{profile.stability_score}/100",
            trend="up" if profile.stability_score > 70 else "down" if profile.stability_score < 40 else "stable",
            description="Чим вище, тим передбачуваніший тиск"
        ))
        
        # Medication insight
        if profile.medication_effectiveness:
            trend = "up" if profile.medication_effectiveness > 15 else "stable"
            insights.append(PatternInsight(
                title="Ефективність ліків",
                value=f"-{profile.medication_effectiveness:.0f}%",
                trend=trend,
                description="Зниження АТ після прийому"
            ))
        
        return insights
    
    # ============= Private helper methods =============
    
    def _analyze_recent_high_readings(
        self,
        measurements: List[MeasurementORM]
    ) -> bool:
        """Check for recent high readings in last 3 days."""
        cutoff = datetime.utcnow() - timedelta(days=3)
        recent = [m for m in measurements if m.measured_at >= cutoff]
        
        high_count = sum(
            1 for m in recent
            if m.systolic > self.HIGH_BP_SYSTOLIC or m.diastolic > self.HIGH_BP_DIASTOLIC
        )
        return high_count >= 2
    
    def _analyze_missed_medications(self, user_id: int) -> int:
        """Count missed medications in last 7 days."""
        cutoff = datetime.utcnow() - timedelta(days=7)
        try:
            missed_count = self._db.query(MedicationIntakeORM).filter(
                and_(
                    MedicationIntakeORM.patient_id == user_id,
                    MedicationIntakeORM.status == "missed",
                    MedicationIntakeORM.scheduled_time >= cutoff
                )
            ).count()
            return missed_count
        except Exception:
            return 0
    
    def _analyze_weather_risk(
        self,
        user_id: int,
        measurements: List[MeasurementORM]
    ) -> bool:
        """Analyze if weather changes pose risk."""
        # Would integrate with weather forecast API
        # Simplified: check user's historical sensitivity
        return False  # Placeholder
    
    def _analyze_pattern_risk(
        self,
        measurements: List[MeasurementORM],
        hours_ahead: int
    ) -> int:
        """Calculate risk based on historical patterns."""
        if not measurements:
            return 0
        
        # Get weekday for prediction time
        prediction_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        weekday = prediction_time.weekday()
        hour = prediction_time.hour
        
        # Check historical readings for this weekday/hour
        similar = [
            m for m in measurements
            if m.measured_at.weekday() == weekday and
            abs(m.measured_at.hour - hour) <= 2
        ]
        
        if not similar:
            return 0
        
        high_ratio = sum(
            1 for m in similar
            if m.systolic > self.HIGH_BP_SYSTOLIC
        ) / len(similar)
        
        return int(high_ratio * 20)  # Up to 20 points
    
    def _days_since_last_measurement(
        self,
        measurements: List[MeasurementORM]
    ) -> int:
        """Days since last measurement."""
        if not measurements:
            return 999
        
        latest = max(m.measured_at for m in measurements)
        delta = datetime.utcnow() - latest
        return delta.days
    
    def _analyze_time_patterns(
        self,
        measurements: List[MeasurementORM]
    ) -> Dict[str, Optional[float]]:
        """Analyze BP patterns by time of day."""
        periods = {
            "morning": [],    # 6-12
            "afternoon": [],  # 12-18
            "evening": [],    # 18-24
            "night": []       # 0-6
        }
        
        for m in measurements:
            hour = m.measured_at.hour
            if 6 <= hour < 12:
                periods["morning"].append(m.systolic)
            elif 12 <= hour < 18:
                periods["afternoon"].append(m.systolic)
            elif 18 <= hour < 24:
                periods["evening"].append(m.systolic)
            else:
                periods["night"].append(m.systolic)
        
        return {
            key: sum(vals) / len(vals) if vals else None
            for key, vals in periods.items()
        }
    
    def _calculate_weather_correlation(
        self,
        measurements: List[MeasurementORM]
    ) -> Optional[float]:
        """Calculate correlation between BP and atmospheric pressure."""
        # Need measurements with weather data
        with_weather = [
            (m.systolic, m.weather_snapshot.pressure_mmhg)
            for m in measurements
            if m.weather_snapshot and m.weather_snapshot.pressure_mmhg
        ]
        
        if len(with_weather) < 5:
            return None
        
        # Pearson correlation
        n = len(with_weather)
        sum_x = sum(x for x, _ in with_weather)
        sum_y = sum(y for _, y in with_weather)
        sum_xy = sum(x * y for x, y in with_weather)
        sum_x2 = sum(x * x for x, _ in with_weather)
        sum_y2 = sum(y * y for _, y in with_weather)
        
        try:
            correlation = (n * sum_xy - sum_x * sum_y) / math.sqrt(
                (n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)
            )
            return correlation
        except (ValueError, ZeroDivisionError):
            return None
    
    def _classify_weather_sensitivity(
        self,
        correlation: Optional[float]
    ) -> str:
        """Classify weather sensitivity level."""
        if correlation is None:
            return "невідомо"
        
        abs_corr = abs(correlation)
        if abs_corr > 0.5:
            return "висока"
        elif abs_corr > 0.3:
            return "середня"
        elif abs_corr > 0.1:
            return "низька"
        return "відсутня"
    
    def _classify_pattern(
        self,
        measurements: List[MeasurementORM],
        time_stats: Dict[str, Optional[float]],
        weather_corr: Optional[float]
    ) -> BPPatternType:
        """Classify user's BP pattern type."""
        # Morning hypertensive check
        if time_stats["morning"] and time_stats["evening"]:
            if time_stats["morning"] > time_stats["evening"] + 10:
                return BPPatternType.MORNING_HYPERTENSIVE
        
        # Weather reactive check
        if weather_corr and abs(weather_corr) > 0.4:
            return BPPatternType.WEATHER_REACTIVE
        
        # Weekend warrior check
        weekday_avg = []
        weekend_avg = []
        for m in measurements:
            if m.measured_at.weekday() < 5:  # Mon-Fri
                weekday_avg.append(m.systolic)
            else:
                weekend_avg.append(m.systolic)
        
        if weekday_avg and weekend_avg:
            wk_avg = sum(weekday_avg) / len(weekday_avg)
            we_avg = sum(weekend_avg) / len(weekend_avg)
            if abs(wk_avg - we_avg) > 10:
                return BPPatternType.WEEKEND_WARRIOR
        
        # Evening spiker check
        if time_stats["evening"] and time_stats["morning"]:
            if time_stats["evening"] > time_stats["morning"] + 10:
                return BPPatternType.EVENING_SPIKER
        
        # Stability check
        variance = self._calculate_variance(measurements)
        if variance < 10:
            return BPPatternType.STABLE
        elif variance > 25:
            return BPPatternType.UNPREDICTABLE
        
        return BPPatternType.STRESS_DEPENDENT
    
    def _get_pattern_info(self, pattern_type: BPPatternType) -> Tuple[str, str]:
        """Get Ukrainian name and description for pattern type."""
        info = {
            BPPatternType.MORNING_HYPERTENSIVE: (
                "🌅 Ранковий гіпертонік",
                "У вас спостерігаються сплески АТ уранці (6-12). "
                "Це пов'язано з природним підйомом кортизолу та активністю симпатичної нервової системи."
            ),
            BPPatternType.WEATHER_REACTIVE: (
                "🌦 Погодний реактив",
                "Ваш тиск чутливий до змін атмосферного тиску. "
                "Ви помічаєте головний біль та зміни самопочуття перед зміною погоди."
            ),
            BPPatternType.STRESS_DEPENDENT: (
                "😰 Стрес-залежний тип",
                "Ваш АТ сильно реагує на емоційний стан. "
                "Стресові ситуації, дедлайни, конфлікти - основні тригери."
            ),
            BPPatternType.MEDICATION_DEPENDENT: (
                "💊 Лікозалежний тип",
                "Ефективність ваших ліків добре відстежується. "
                "Важливо не пропускати прийоми - відразу помітно на показниках."
            ),
            BPPatternType.EVENING_SPIKER: (
                "🌆 Вечірній спікер",
                "Сплески АТ ввечері (після 18:00). "
                "Може бути пов'язано з втомою, прийомом їжі чи відкладенням стресу."
            ),
            BPPatternType.WEEKEND_WARRIOR: (
                "📅 Вихідний тип",
                "Різниця між робочими днями та вихідними. "
                "Робочий стрес сильно впливає на ваші показники."
            ),
            BPPatternType.STABLE: (
                "✅ Стабільний тип",
                "Ваш АТ добре контрольований і передбачуваний. "
                "Ви знаєте свої тригери і успішно їх уникаєте."
            ),
            BPPatternType.UNPREDICTABLE: (
                "❓ Непередбачуваний тип",
                "Ваш АТ має високу варіабельність. "
                "Потрібен ретельний аналіз тригерів та коригування терапії."
            ),
        }
        return info.get(pattern_type, ("Невідомий тип", ""))
    
    def _calculate_medication_effectiveness(
        self,
        user_id: int
    ) -> Optional[float]:
        """Calculate how effective medications are."""
        # Simplified: compare readings before and after medication times
        # Would need more sophisticated analysis in production
        return None  # Placeholder
    
    def _calculate_variance(
        self,
        measurements: List[MeasurementORM]
    ) -> float:
        """Calculate standard deviation of systolic BP."""
        if len(measurements) < 2:
            return 0
        
        values = [m.systolic for m in measurements]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _identify_triggers(self, measurements: List[MeasurementORM]) -> List[str]:
        """Identify common triggers from notes."""
        # Simple keyword matching in notes
        trigger_keywords = {
            "кава": "☕ Кава",
            "кофе": "☕ Кава",
            "сіль": "🧂 Солона їжа",
            "солон": "🧂 Солона їжа",
            "спорт": "🏃 Фізичне навантаження",
            "біг": "🏃 Фізичне навантаження",
            "стрес": "😰 Стрес",
            "робот": "💼 Робочий стрес",
            "сон": "😴 Поганий сон",
            "алког": "🍷 Алкоголь",
        }
        
        triggers = set()
        for m in measurements:
            if m.notes:
                notes_lower = m.notes.lower()
                for keyword, trigger in trigger_keywords.items():
                    if keyword in notes_lower:
                        triggers.add(trigger)
        
        return list(triggers)[:5]  # Top 5 triggers
    
    def _generate_insights(
        self,
        pattern_type: BPPatternType,
        time_stats: Dict[str, Optional[float]],
        weather_corr: Optional[float],
        med_effect: Optional[float],
        triggers: List[str]
    ) -> List[str]:
        """Generate personalized insights."""
        insights = []
        
        # Pattern-based insights
        if pattern_type == BPPatternType.MORNING_HYPERTENSIVE:
            insights.append("Приймайте ліки ввечері - це зменшить ранковий сплеск")
        elif pattern_type == BPPatternType.WEATHER_REACTIVE:
            insights.append("Перевіряйте прогноз погоди - вимірюйтесь до змін тиску")
        elif pattern_type == BPPatternType.EVENING_SPIKER:
            insights.append("Уникайте важкої їжі після 18:00 та зменшіть навантаження ввечері")
        
        # Weather insight
        if weather_corr and weather_corr > 0.3:
            insights.append("При падінні атм. тиску ваш АТ зазвичай підвищується")
        elif weather_corr and weather_corr < -0.3:
            insights.append("При підвищенні атм. тиску ваш АТ зазвичай знижується")
        
        # Trigger-based insights
        if "☕ Кава" in triggers:
            insights.append("Кава - ваш головний тригер. Спробуйте обмежити до 1 чашки до 14:00")
        if "😰 Стрес" in triggers:
            insights.append("Рекомендуємо техніки релаксації: дихальні вправи, медитація")
        
        if not insights:
            insights.append("Продовжуйте регулярний моніторинг для кращого аналізу")
        
        return insights
    
    def _create_insufficient_data_profile(self) -> DNAProfile:
        """Create profile when insufficient data."""
        return DNAProfile(
            pattern_type=BPPatternType.UNPREDICTABLE,
            pattern_name="❓ Недостатньо даних",
            pattern_description="Для аналізу потрібно мінімум 10 вимірювань за 90 днів.",
            morning_avg=None,
            afternoon_avg=None,
            evening_avg=None,
            night_avg=None,
            weather_correlation=None,
            weather_sensitivity="невідомо",
            medication_effectiveness=None,
            stability_score=0,
            variance=0,
            triggers=[],
            insights=["Зробіть більше вимірювань для персонального аналізу"],
            generated_at=datetime.utcnow(),
            data_days=0
        )
