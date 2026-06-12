"""Unit tests for app/services/validation_service.py — no database required."""
from __future__ import annotations

import pytest

from app.services.validation_service import ValidationError, ValidationService


@pytest.fixture
def svc() -> ValidationService:
    return ValidationService()


# ---------------------------------------------------------------------------
# validate_measurement
# ---------------------------------------------------------------------------

class TestValidateMeasurement:
    def test_valid(self, svc):
        assert svc.validate_measurement(120, 80, 72, "2024-01-01 10:00") == []

    def test_systolic_too_low(self, svc):
        errors = svc.validate_measurement(50, 40, 72, "2024-01-01 10:00")
        fields = [e.field for e in errors]
        assert "systolic" in fields

    def test_systolic_too_high(self, svc):
        errors = svc.validate_measurement(250, 80, 72, "2024-01-01 10:00")
        assert any(e.field == "systolic" for e in errors)

    def test_diastolic_too_low(self, svc):
        errors = svc.validate_measurement(120, 30, 72, "2024-01-01 10:00")
        assert any(e.field == "diastolic" for e in errors)

    def test_diastolic_too_high(self, svc):
        errors = svc.validate_measurement(120, 160, 72, "2024-01-01 10:00")
        assert any(e.field == "diastolic" for e in errors)

    def test_systolic_less_than_diastolic(self, svc):
        errors = svc.validate_measurement(80, 100, 72, "2024-01-01 10:00")
        assert any(e.field == "systolic" for e in errors)

    def test_systolic_equals_diastolic(self, svc):
        errors = svc.validate_measurement(80, 80, 72, "2024-01-01 10:00")
        assert any(e.field == "systolic" for e in errors)

    def test_pulse_too_low(self, svc):
        errors = svc.validate_measurement(120, 80, 20, "2024-01-01 10:00")
        assert any(e.field == "pulse" for e in errors)

    def test_pulse_too_high(self, svc):
        errors = svc.validate_measurement(120, 80, 250, "2024-01-01 10:00")
        assert any(e.field == "pulse" for e in errors)

    def test_invalid_timestamp_format(self, svc):
        errors = svc.validate_measurement(120, 80, 72, "01-01-2024")
        assert any(e.field == "timestamp" for e in errors)

    def test_empty_timestamp(self, svc):
        errors = svc.validate_measurement(120, 80, 72, "")
        assert any(e.field == "timestamp" for e in errors)

    def test_multiple_errors_accumulate(self, svc):
        errors = svc.validate_measurement(50, 200, 250, "bad-date")
        assert len(errors) >= 3

    def test_boundary_systolic_min(self, svc):
        assert svc.validate_measurement(60, 40, 72, "2024-01-01 10:00") == []

    def test_boundary_systolic_max(self, svc):
        assert svc.validate_measurement(240, 80, 72, "2024-01-01 10:00") == []

    def test_boundary_pulse_min(self, svc):
        assert svc.validate_measurement(120, 80, 35, "2024-01-01 10:00") == []

    def test_boundary_pulse_max(self, svc):
        assert svc.validate_measurement(120, 80, 220, "2024-01-01 10:00") == []


# ---------------------------------------------------------------------------
# validate_user_profile
# ---------------------------------------------------------------------------

class TestValidateUserProfile:
    def test_valid(self, svc):
        assert svc.validate_user_profile("Іван Петренко", 30, 120, 80, 72) == []

    def test_name_too_short(self, svc):
        errors = svc.validate_user_profile("І", 30, 120, 80, 72)
        assert any(e.field == "name" for e in errors)

    def test_name_empty(self, svc):
        errors = svc.validate_user_profile("", 30, 120, 80, 72)
        assert any(e.field == "name" for e in errors)

    def test_age_zero(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 0, 120, 80, 72)
        assert any(e.field == "age" for e in errors)

    def test_age_over_max(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 130, 120, 80, 72)
        assert any(e.field == "age" for e in errors)

    def test_systolic_too_low(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 30, 70, 80, 72)
        assert any(e.field == "target_systolic" for e in errors)

    def test_target_systolic_lte_diastolic(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 30, 80, 90, 72)
        assert any(e.field == "target_systolic" for e in errors)

    def test_pulse_too_low(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 30, 120, 80, 30)
        assert any(e.field == "target_pulse" for e in errors)

    def test_pulse_too_high(self, svc):
        errors = svc.validate_user_profile("Іван Петренко", 30, 120, 80, 200)
        assert any(e.field == "target_pulse" for e in errors)


# ---------------------------------------------------------------------------
# format_errors
# ---------------------------------------------------------------------------

class TestFormatErrors:
    def test_empty_list(self, svc):
        assert svc.format_errors([]) == ""

    def test_single_error(self, svc):
        errors = [ValidationError("systolic", "Systolic too high")]
        result = svc.format_errors(errors)
        assert "Systolic too high" in result
        assert result.startswith("•")

    def test_multiple_errors(self, svc):
        errors = [
            ValidationError("systolic", "A"),
            ValidationError("diastolic", "B"),
        ]
        result = svc.format_errors(errors)
        assert "A" in result
        assert "B" in result
        assert result.count("•") == 2
