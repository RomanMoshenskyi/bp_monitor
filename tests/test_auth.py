"""Unit tests for app/auth.py — no database required."""
from __future__ import annotations

import pytest

from app.auth import (
    _hash_password,
    _validate_password_strength,
    _verify_password,
)


# ---------------------------------------------------------------------------
# _validate_password_strength
# ---------------------------------------------------------------------------

class TestValidatePasswordStrength:
    def test_valid_password(self):
        _validate_password_strength("Secure1Pass")  # must not raise

    def test_too_short(self):
        with pytest.raises(ValueError, match="8 символів"):
            _validate_password_strength("Ab1")

    def test_exactly_8_chars(self):
        _validate_password_strength("Abcdef1g")  # must not raise

    def test_no_uppercase(self):
        with pytest.raises(ValueError, match="велику літеру"):
            _validate_password_strength("abcdef123")

    def test_no_lowercase(self):
        with pytest.raises(ValueError, match="малу літеру"):
            _validate_password_strength("ABCDEF123")

    def test_no_digit(self):
        with pytest.raises(ValueError, match="цифру"):
            _validate_password_strength("Abcdefgh")

    def test_all_conditions_met(self):
        for pwd in ("AdminPass123", "DoctorPass123", "PatientPass123"):
            _validate_password_strength(pwd)  # must not raise


# ---------------------------------------------------------------------------
# _hash_password / _verify_password
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_not_plaintext(self):
        hashed = _hash_password("Secure1Pass")
        assert hashed != "Secure1Pass"
        assert "$" in hashed

    def test_verify_correct(self):
        pwd = "Secure1Pass"
        assert _verify_password(pwd, _hash_password(pwd)) is True

    def test_verify_wrong(self):
        assert _verify_password("WrongPass1", _hash_password("Secure1Pass")) is False

    def test_hash_is_deterministic_with_salt_part(self):
        h1 = _hash_password("Secure1Pass")
        h2 = _hash_password("Secure1Pass")
        # Salt is random, so hashes differ, but both verify correctly
        assert h1 != h2
        assert _verify_password("Secure1Pass", h1)
        assert _verify_password("Secure1Pass", h2)

    def test_verify_corrupt_hash(self):
        assert _verify_password("Secure1Pass", "notahash") is False

    def test_verify_empty_password(self):
        hashed = _hash_password("Secure1Pass")
        assert _verify_password("", hashed) is False
