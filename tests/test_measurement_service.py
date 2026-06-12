"""Unit tests for MeasurementService — no database required."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.measurement_service import MeasurementService
from app.models import Measurement


def _make_storage():
    storage = MagicMock()
    storage.get_measurements.return_value = []
    return storage


def _make_service(storage=None):
    return MeasurementService(storage or _make_storage())


# ---------------------------------------------------------------------------
# create_measurement
# ---------------------------------------------------------------------------

class TestCreateMeasurement:
    def test_valid_creates_and_returns_measurement(self):
        storage = _make_storage()
        svc = _make_service(storage)
        m = svc.create_measurement(
            timestamp="2024-06-01 10:00",
            systolic=120,
            diastolic=80,
            pulse=72,
            mood="Спокійний",
            notes="",
            atmospheric_pressure=750,
            medication_taken=False,
            activity_level="Низька",
        )
        assert m.systolic == 120
        assert m.diastolic == 80
        assert m.pulse == 72
        storage.add_measurement.assert_called_once()

    def test_invalid_raises_value_error(self):
        svc = _make_service()
        with pytest.raises(ValueError):
            svc.create_measurement(
                timestamp="bad-date",
                systolic=50,
                diastolic=200,
                pulse=300,
                mood="Спокійний",
                notes="",
                atmospheric_pressure=None,
                medication_taken=False,
                activity_level="Низька",
            )

    def test_storage_not_called_on_validation_error(self):
        storage = _make_storage()
        svc = _make_service(storage)
        with pytest.raises(ValueError):
            svc.create_measurement(
                timestamp="2024-06-01 10:00",
                systolic=50,
                diastolic=30,
                pulse=72,
                mood="Спокійний",
                notes="",
                atmospheric_pressure=None,
                medication_taken=False,
                activity_level="Низька",
            )
        storage.add_measurement.assert_not_called()

    def test_id_is_generated(self):
        svc = _make_service()
        m = svc.create_measurement(
            timestamp="2024-06-01 10:00",
            systolic=120,
            diastolic=80,
            pulse=72,
            mood="Спокійний",
            notes="",
            atmospheric_pressure=None,
            medication_taken=False,
            activity_level="Низька",
        )
        assert m.id and len(m.id) == 8

    def test_patient_id_forwarded(self):
        storage = _make_storage()
        svc = _make_service(storage)
        svc.create_measurement(
            timestamp="2024-06-01 10:00",
            systolic=120,
            diastolic=80,
            pulse=72,
            mood="Спокійний",
            notes="",
            atmospheric_pressure=None,
            medication_taken=False,
            activity_level="Низька",
            patient_id=99,
        )
        _, call_kwargs = storage.add_measurement.call_args
        assert call_kwargs.get("patient_id") == 99 or storage.add_measurement.call_args[0][1] == 99


# ---------------------------------------------------------------------------
# delete_measurement
# ---------------------------------------------------------------------------

class TestDeleteMeasurement:
    def test_delegates_to_storage(self):
        storage = _make_storage()
        svc = _make_service(storage)
        svc.delete_measurement("abc12345")
        storage.delete_measurement.assert_called_once_with("abc12345", None)

    def test_with_patient_id(self):
        storage = _make_storage()
        svc = _make_service(storage)
        svc.delete_measurement("abc12345", patient_id=7)
        storage.delete_measurement.assert_called_once_with("abc12345", 7)


# ---------------------------------------------------------------------------
# get_measurements / get_summary
# ---------------------------------------------------------------------------

class TestGetMeasurements:
    def test_returns_storage_result(self):
        storage = _make_storage()
        fake = [Measurement("x", "2024-01-01 10:00", 120, 80, 72)]
        storage.get_measurements.return_value = fake
        svc = _make_service(storage)
        result = svc.get_measurements()
        assert result is fake

    def test_get_summary_empty(self):
        svc = _make_service()
        s = svc.get_summary()
        assert s["count"] == 0
