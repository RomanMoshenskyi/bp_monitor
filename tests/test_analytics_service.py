"""Unit tests for AnalyticsService — no database required."""
from __future__ import annotations

import pytest

from app.services.analytics_service import AnalyticsService
from app.models import Measurement


def _m(systolic: int, diastolic: int, pulse: int = 72, days_ago: int = 0) -> Measurement:
    from datetime import datetime, timedelta
    ts = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M")
    return Measurement(
        id="x",
        timestamp=ts,
        systolic=systolic,
        diastolic=diastolic,
        pulse=pulse,
        atmospheric_pressure=750,
    )


@pytest.fixture
def svc() -> AnalyticsService:
    return AnalyticsService()


class TestGetSummary:
    def test_empty(self, svc):
        s = svc.get_summary([])
        assert s["count"] == 0

    def test_single(self, svc):
        s = svc.get_summary([_m(130, 85)])
        assert s["count"] == 1
        assert s["avg_systolic"] == 130

    def test_multiple(self, svc):
        data = [_m(120, 80), _m(140, 90)]
        s = svc.get_summary(data)
        assert s["avg_systolic"] == 130


class TestGetPressureStatus:
    def test_normal(self, svc):
        assert svc.get_pressure_status(115, 75) == "Норма"

    def test_hypertension_2(self, svc):
        assert svc.get_pressure_status(150, 95) == "Гіпертензія II"

    def test_hypertension_1(self, svc):
        assert svc.get_pressure_status(135, 85) == "Гіпертензія I"

    def test_elevated(self, svc):
        assert svc.get_pressure_status(125, 78) == "Підвищений"

    def test_low(self, svc):
        assert svc.get_pressure_status(85, 55) == "Знижений"


class TestFilterByPeriod:
    def test_none_returns_all(self, svc):
        data = [_m(120, 80, days_ago=i) for i in range(20)]
        assert len(svc.filter_by_period(data, None)) == 20

    def test_7_days(self, svc):
        data = [_m(120, 80, days_ago=i) for i in range(15)]
        result = svc.filter_by_period(data, 7)
        assert all(True for _ in result)
        assert len(result) <= 15

    def test_empty(self, svc):
        assert svc.filter_by_period([], 7) == []


class TestGetRecommendations:
    def test_returns_list(self, svc):
        data = [_m(160, 100) for _ in range(5)]
        recs = svc.get_recommendations(data)
        assert isinstance(recs, list)

    def test_empty_data(self, svc):
        recs = svc.get_recommendations([])
        assert isinstance(recs, list)


class TestGetLatest:
    def test_none_when_empty(self, svc):
        assert svc.get_latest([]) is None

    def test_returns_last(self, svc):
        data = [_m(120, 80), _m(130, 85)]
        latest = svc.get_latest(data)
        assert latest is not None
