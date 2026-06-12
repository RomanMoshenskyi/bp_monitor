"""AnalysisService - statistical analysis with Pearson correlation from diploma."""
from __future__ import annotations

import math
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any

import numpy as np

from app.domain.entities import MeasurementORM, ThresholdProfileORM, SeverityLevel
from app.application.dto import (
    MeasurementStatsDTO,
    CorrelationResultDTO,
    AnalysisResultDTO,
    MeasurementDTO,
)

_logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Statistical analysis service.
    
    From diploma (section 3.4.4, formula 3.2):
    - Pearson correlation between BP and atmospheric pressure
    - r = Σ((xi - x̄)(yi - ȳ)) / √(Σ(xi - x̄)² × Σ(yi - ȳ)²)
    """
    
    def calculate_statistics(self, measurements: List[MeasurementORM]) -> MeasurementStatsDTO:
        """Calculate basic statistics for measurements."""
        if not measurements:
            return MeasurementStatsDTO(
                count=0,
                avg_systolic=0.0,
                min_systolic=0,
                max_systolic=0,
                avg_diastolic=0.0,
                min_diastolic=0,
                max_diastolic=0,
                avg_pulse=None,
            )
        
        systolics = [m.systolic for m in measurements]
        diastolics = [m.diastolic for m in measurements]
        pulses = [m.pulse for m in measurements if m.pulse is not None]
        
        return MeasurementStatsDTO(
            count=len(measurements),
            avg_systolic=sum(systolics) / len(systolics),
            min_systolic=min(systolics),
            max_systolic=max(systolics),
            avg_diastolic=sum(diastolics) / len(diastolics),
            min_diastolic=min(diastolics),
            max_diastolic=max(diastolics),
            avg_pulse=sum(pulses) / len(pulses) if pulses else None,
        )
    
    def calculate_pearson_correlation(
        self,
        bp_values: List[float],
        pressure_values: List[float]
    ) -> Optional[CorrelationResultDTO]:
        """
        Calculate Pearson correlation coefficient.
        
        Formula from diploma (3.2):
        r = Σ((xi - x̄)(yi - ȳ)) / √(Σ(xi - x̄)² × Σ(yi - ȳ)²)
        
        Args:
            bp_values: List of blood pressure values (systolic)
            pressure_values: List of atmospheric pressure values (mmHg)
        
        Returns:
            CorrelationResultDTO with coefficient and interpretation
        """
        if len(bp_values) != len(pressure_values) or len(bp_values) < 3:
            _logger.warning(f"Insufficient data for correlation: {len(bp_values)} points")
            return None
        
        n = len(bp_values)
        
        # Calculate means (x̄, ȳ)
        x_mean = sum(bp_values) / n
        y_mean = sum(pressure_values) / n
        
        # Calculate numerator Σ((xi - x̄)(yi - ȳ))
        numerator = sum(
            (x - x_mean) * (y - y_mean)
            for x, y in zip(bp_values, pressure_values)
        )
        
        # Calculate denominator √(Σ(xi - x̄)² × Σ(yi - ȳ)²)
        sum_squared_x = sum((x - x_mean) ** 2 for x in bp_values)
        sum_squared_y = sum((y - y_mean) ** 2 for y in pressure_values)
        
        denominator = math.sqrt(sum_squared_x * sum_squared_y)
        
        if denominator == 0:
            _logger.warning("Zero denominator in correlation calculation")
            return None
        
        r = numerator / denominator
        
        # Interpretation (from diploma)
        if abs(r) < 0.3:
            interpretation = "Слабкий зв'язок - атмосферний тиск мало впливає на АТ"
        elif abs(r) < 0.7:
            interpretation = "Помірний зв'язок - можливий вплив атмосферного тиску на АТ"
        else:
            interpretation = "Сильний зв'язок - атмосферний тиск суттєво впливає на АТ"
        
        # Using numpy for p-value (if available)
        p_value = None
        try:
            from scipy import stats
            _, p_value = stats.pearsonr(bp_values, pressure_values)
        except ImportError:
            pass  # scipy not required
        
        return CorrelationResultDTO(
            correlation_coefficient=round(r, 4),
            p_value=p_value,
            sample_size=n,
            interpretation=interpretation,
            systolic_mean=round(x_mean, 2),
            pressure_mean=round(y_mean, 2),
        )
    
    def analyze_measurements(
        self,
        patient_id: int,
        measurements: List[MeasurementORM],
        threshold_profile: Optional[ThresholdProfileORM] = None,
    ) -> AnalysisResultDTO:
        """
        Complete analysis of measurements.
        
        From diploma: combines statistics, correlation, and recommendations.
        """
        if not measurements:
            return AnalysisResultDTO(
                patient_id=patient_id,
                period_start=date.today(),
                period_end=date.today(),
                stats=self.calculate_statistics([]),
                bp_weather_correlation=None,
                threshold_status="unknown",
                warnings=["Немає даних для аналізу"],
                recommendations=[],
            )
        
        # Date range
        dates = [m.measured_at.date() for m in measurements if m.measured_at]
        period_start = min(dates) if dates else date.today()
        period_end = max(dates) if dates else date.today()
        
        # Statistics
        stats = self.calculate_statistics(measurements)
        
        # BP-Weather correlation (only for measurements with weather data)
        measurements_with_weather = [
            m for m in measurements 
            if m.weather_snapshot_id is not None and m.weather_snapshot
        ]
        
        correlation = None
        if len(measurements_with_weather) >= 3:
            bp_values = [float(m.systolic) for m in measurements_with_weather]
            pressure_values = [float(m.weather_snapshot.pressure_mmhg) for m in measurements_with_weather]
            correlation = self.calculate_pearson_correlation(bp_values, pressure_values)
        
        # Threshold check
        threshold_status = "normal"
        warnings = []
        recommendations = []
        
        if threshold_profile:
            latest = max(measurements, key=lambda m: m.measured_at or datetime.min)
            check = threshold_profile.check_measurement(
                latest.systolic, latest.diastolic, latest.pulse
            )
            threshold_status = check["overall_status"]
            warnings = check["warnings"]
            
            # Generate recommendations based on status
            if threshold_status == "warning":
                recommendations.append("Зверніть увагу на показники артеріального тиску")
        
        # Add correlation-based recommendation
        if correlation and correlation.is_significant(0.5):
            recommendations.append(
                f"Виявлено зв'язок з атмосферним тиском (r={correlation.correlation_coefficient:.2f}). "
                f"{correlation.interpretation}"
            )
        
        return AnalysisResultDTO(
            patient_id=patient_id,
            period_start=period_start,
            period_end=period_end,
            stats=stats,
            bp_weather_correlation=correlation,
            threshold_status=threshold_status,
            warnings=warnings,
            recommendations=recommendations,
        )
    
    def evaluate_status(self, systolic: int, diastolic: int) -> str:
        """Quick status evaluation without thresholds."""
        if systolic > 140 or diastolic > 90:
            return "high"
        elif systolic < 90 or diastolic < 60:
            return "low"
        return "normal"
    
    def detect_anomalies(
        self,
        measurements: List[MeasurementORM],
        threshold_multiplier: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalous measurements using standard deviation."""
        if len(measurements) < 5:
            return []
        
        systolics = [m.systolic for m in measurements]
        diastolics = [m.diastolic for m in measurements]
        
        # Calculate means and std
        sys_mean = sum(systolics) / len(systolics)
        dia_mean = sum(diastolics) / len(diastolics)
        
        sys_std = math.sqrt(sum((x - sys_mean) ** 2 for x in systolics) / len(systolics))
        dia_std = math.sqrt(sum((x - dia_mean) ** 2 for x in diastolics) / len(diastolics))
        
        anomalies = []
        for m in measurements:
            sys_z = abs(m.systolic - sys_mean) / sys_std if sys_std > 0 else 0
            dia_z = abs(m.diastolic - dia_mean) / dia_std if dia_std > 0 else 0
            
            if sys_z > threshold_multiplier or dia_z > threshold_multiplier:
                anomalies.append({
                    "measurement_id": m.id,
                    "measured_at": m.measured_at.isoformat() if m.measured_at else None,
                    "systolic": m.systolic,
                    "diastolic": m.diastolic,
                    "systolic_z_score": round(sys_z, 2),
                    "diastolic_z_score": round(dia_z, 2),
                    "reason": "Відхилення від середнього значення",
                })
        
        return anomalies
