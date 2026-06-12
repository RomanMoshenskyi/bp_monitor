"""Unit tests for app/weather.py — no real HTTP calls."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.weather import (
    _cache,
    _cache_lock,
    _CACHE_TTL,
    fetch_atmospheric_pressure_mmhg,
    invalidate_weather_cache,
    nearest_city,
)


def _clear_cache():
    with _cache_lock:
        _cache.clear()


@pytest.fixture(autouse=True)
def clean_cache():
    _clear_cache()
    yield
    _clear_cache()


class TestNearestCity:
    def test_kyiv_coords(self):
        assert nearest_city(50.45, 30.52) == "Київ"

    def test_lviv_coords(self):
        city = nearest_city(49.84, 24.03)
        assert city == "Львів"


class TestFetchAtmosphericPressure:
    def test_returns_int_on_success(self):
        with patch("app.weather._fetch_pressure_raw", return_value=750):
            result = fetch_atmospheric_pressure_mmhg("Київ")
        assert result == 750
        assert isinstance(result, int)

    def test_caches_result(self):
        call_count = {"n": 0}

        def fake_fetch(lat, lon):
            call_count["n"] += 1
            return 750

        with patch("app.weather._fetch_pressure_raw", side_effect=fake_fetch):
            fetch_atmospheric_pressure_mmhg("Київ")
            fetch_atmospheric_pressure_mmhg("Київ")

        assert call_count["n"] == 1

    def test_cache_expires(self):
        with patch("app.weather._fetch_pressure_raw", return_value=750):
            fetch_atmospheric_pressure_mmhg("Київ")

        with _cache_lock:
            _cache["Київ"] = (750, datetime.now() - _CACHE_TTL - timedelta(seconds=1))

        with patch("app.weather._fetch_pressure_raw", return_value=760) as mock_fetch:
            result = fetch_atmospheric_pressure_mmhg("Київ")

        assert result == 760

    def test_returns_none_after_all_retries_fail(self):
        import urllib.error
        with patch(
            "app.weather._fetch_pressure_raw",
            side_effect=urllib.error.URLError("network error"),
        ), patch("app.weather.time.sleep"):
            result = fetch_atmospheric_pressure_mmhg("Львів")
        assert result is None

    def test_retries_on_failure_then_succeeds(self):
        import urllib.error
        attempts = {"n": 0}

        def flaky(lat, lon):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise urllib.error.URLError("timeout")
            return 755

        with patch("app.weather._fetch_pressure_raw", side_effect=flaky), \
             patch("app.weather.time.sleep"):
            result = fetch_atmospheric_pressure_mmhg("Харків")

        assert result == 755
        assert attempts["n"] == 2


class TestInvalidateCache:
    def test_invalidate_single_city(self):
        with _cache_lock:
            _cache["Київ"] = (750, datetime.now())
            _cache["Львів"] = (748, datetime.now())
        invalidate_weather_cache("Київ")
        with _cache_lock:
            assert "Київ" not in _cache
            assert "Львів" in _cache

    def test_invalidate_all(self):
        with _cache_lock:
            _cache["Київ"] = (750, datetime.now())
            _cache["Львів"] = (748, datetime.now())
        invalidate_weather_cache()
        with _cache_lock:
            assert len(_cache) == 0
