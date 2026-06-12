"""Analysis DTOs - Pearson correlation from diploma."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Dict, Any


@dataclass
class MeasurementStatsDTO:
    """Statistics for measurements."""
    count: int
    avg_systolic: float
    min_systolic: int
    max_systolic: int
    avg_diastolic: float
    min_diastolic: int
    max_diastolic: int
    avg_pulse: Optional[float]


@dataclass
class CorrelationResultDTO:
    """
    Pearson correlation result from diploma formula 3.2.
    
    r = Σ((xi - x̄)(yi - ȳ)) / √(Σ(xi - x̄)² × Σ(yi - ȳ)²)
    """
    correlation_coefficient: float  # r value (-1 to 1)
    p_value: Optional[float]  # Statistical significance
    sample_size: int  # n
    interpretation: str  # Text summary from diploma
    
    # Intermediate values (for debugging/display)
    systolic_mean: float  # x̄
    pressure_mean: float  # ȳ
    
    def is_significant(self, threshold: float = 0.5) -> bool:
        """Check if correlation is significant."""
        return abs(self.correlation_coefficient) >= threshold


@dataclass
class AnalysisResultDTO:
    """Complete analysis result."""
    patient_id: int
    period_start: date
    period_end: date
    
    # Basic stats
    stats: MeasurementStatsDTO
    
    # Correlation analysis (diploma 3.2)
    bp_weather_correlation: Optional[CorrelationResultDTO]
    
    # Threshold status
    threshold_status: str  # normal, warning, critical
    warnings: List[str]
    
    # Recommendations generated
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "stats": {
                "count": self.stats.count,
                "systolic": {
                    "avg": self.stats.avg_systolic,
                    "min": self.stats.min_systolic,
                    "max": self.stats.max_systolic,
                },
                "diastolic": {
                    "avg": self.stats.avg_diastolic,
                    "min": self.stats.min_diastolic,
                    "max": self.stats.max_diastolic,
                },
            },
            "correlation": {
                "coefficient": self.bp_weather_correlation.correlation_coefficient if self.bp_weather_correlation else None,
                "interpretation": self.bp_weather_correlation.interpretation if self.bp_weather_correlation else None,
            },
            "status": self.threshold_status,
            "warnings": self.warnings,
        }
