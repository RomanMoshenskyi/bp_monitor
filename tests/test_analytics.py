"""Unit tests for app/analytics.py — no database required."""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.analytics import (
    average,
    correlation_atmospheric,
    filter_by_days,
    generate_recommendations,
    latest_measurement,
    pressure_status,
    summary,
)
from app.models import Measurement


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _m(mid: str, days_ago: int, systolic: int, diastolic: int, pulse: int = 72,
        atm: int | None = None) -> Measurement:
    ts = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")
    return Measurement(
        id=mid, timestamp=ts, systolic=systolic,
        diastolic=diastolic, pulse=pulse, atmospheric_pressure=atm,
    )


# ---------------------------------------------------------------------------
# pressure_status
# ---------------------------------------------------------------------------

class TestPressureStatus:
    def test_normal(self):
        assert pressure_status(115, 75) == "Норма"

    def test_elevated(self):
        assert pressure_status(125, 78) == "Підвищений"

    def test_hypertension_1(self):
        assert pressure_status(135, 85) == "Гіпертензія I"

    def test_hypertension_2(self):
        assert pressure_status(145, 95) == "Гіпертензія II"

    def test_low(self):
        assert pressure_status(85, 55) == "Знижений"

    def test_high_systolic_triggers_h2(self):
        assert pressure_status(160, 70) == "Гіпертензія II"

    def test_high_diastolic_triggers_h2(self):
        assert pressure_status(130, 92) == "Гіпертензія II"


# ---------------------------------------------------------------------------
# average
# ---------------------------------------------------------------------------

class TestAverage:
    def test_basic(self):
        assert average([1.0, 2.0, 3.0]) == 2.0

    def test_empty(self):
        assert average([]) == 0.0

    def test_single(self):
        assert average([42.0]) == 42.0


# ---------------------------------------------------------------------------
# filter_by_days
# ---------------------------------------------------------------------------

class TestFilterByDays:
    def test_filters_old_out(self):
        ms = [_m("1", 1, 120, 80), _m("2", 10, 125, 82)]
        result = filter_by_days(ms, 7)
        assert len(result) == 1
        assert result[0].id == "1"

    def test_empty_input(self):
        assert filter_by_days([], 7) == []

    def test_keeps_all_when_recent(self):
        ms = [_m("1", 1, 120, 80), _m("2", 3, 125, 82)]
        assert len(filter_by_days(ms, 7)) == 2

    def test_boundary_inclusive(self):
        ms = [_m("1", 7, 120, 80)]
        assert len(filter_by_days(ms, 7)) == 1


# ---------------------------------------------------------------------------
# latest_measurement
# ---------------------------------------------------------------------------

class TestLatestMeasurement:
    def test_returns_most_recent(self):
        ms = [_m("1", 5, 120, 80), _m("2", 1, 130, 85)]
        assert latest_measurement(ms).id == "2"

    def test_empty(self):
        assert latest_measurement([]) is None

    def test_single(self):
        ms = [_m("1", 3, 120, 80)]
        assert latest_measurement(ms).id == "1"


# ---------------------------------------------------------------------------
# correlation_atmospheric
# ---------------------------------------------------------------------------

class TestCorrelationAtmospheric:
    def test_positive_correlation(self):
        ms = [
            _m("1", 3, 120, 80, atm=740),
            _m("2", 2, 125, 82, atm=745),
            _m("3", 1, 130, 85, atm=750),
        ]
        corr = correlation_atmospheric(ms)
        assert corr is not None
        assert corr > 0.9

    def test_insufficient_data_returns_none(self):
        ms = [_m("1", 1, 120, 80, atm=745), _m("2", 2, 125, 82, atm=748)]
        assert correlation_atmospheric(ms) is None

    def test_no_atmospheric_data_returns_none(self):
        ms = [_m("1", 1, 120, 80), _m("2", 2, 125, 82), _m("3", 3, 130, 85)]
        assert correlation_atmospheric(ms) is None

    def test_result_in_range(self):
        ms = [
            _m("1", 5, 115, 75, atm=740),
            _m("2", 4, 130, 85, atm=738),
            _m("3", 3, 120, 78, atm=745),
        ]
        corr = correlation_atmospheric(ms)
        if corr is not None:
            assert -1.0 <= corr <= 1.0

    def test_constant_atm_returns_none(self):
        ms = [
            _m("1", 3, 120, 80, atm=745),
            _m("2", 2, 125, 82, atm=745),
            _m("3", 1, 130, 85, atm=745),
        ]
        assert correlation_atmospheric(ms) is None


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_empty(self):
        s = summary([])
        assert s["count"] == 0
        assert s["avg_systolic"] == 0
        assert s["correlation"] is None
        assert s["pressure_trend"] == "Немає даних"

    def test_single(self):
        ms = [_m("1", 0, 120, 80, pulse=72, atm=None)]
        s = summary(ms)
        assert s["count"] == 1
        assert s["avg_systolic"] == 120.0
        assert s["avg_diastolic"] == 80.0
        assert s["avg_pulse"] == 72.0

    def test_trend_rising(self):
        ms = [_m(str(i), 10 - i, 110 + i * 5, 70 + i) for i in range(5)]
        s = summary(ms)
        assert s["pressure_trend"] == "До зростання"

    def test_trend_falling(self):
        ms = [_m(str(i), 10 - i, 140 - i * 5, 90 - i) for i in range(5)]
        s = summary(ms)
        assert s["pressure_trend"] == "До зниження"

    def test_trend_stable(self):
        ms = [_m(str(i), 10 - i, 120, 80) for i in range(5)]
        s = summary(ms)
        assert s["pressure_trend"] == "Стабільний"


# ---------------------------------------------------------------------------
# generate_recommendations
# ---------------------------------------------------------------------------

class TestGenerateRecommendations:
    def test_empty_measurements(self):
        recs = generate_recommendations([])
        assert len(recs) > 0
        assert any("перше вимірювання" in r.lower() for r in recs)

    def test_high_pressure_triggers_warning(self):
        ms = [_m("1", 0, 150, 95, pulse=80)]
        recs = generate_recommendations(ms)
        assert any("підвищені значення" in r.lower() for r in recs)

    def test_low_pressure_triggers_warning(self):
        ms = [_m("1", 0, 88, 58, pulse=60)]
        recs = generate_recommendations(ms)
        assert any("знижені" in r.lower() for r in recs)

    def test_result_capped_at_4(self):
        ms = [_m(str(i), i, 145, 95, pulse=90, atm=745 + i) for i in range(10)]
        recs = generate_recommendations(ms)
        assert len(recs) <= 4
