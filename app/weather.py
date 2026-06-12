from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Tuple

# Координати міст України (назва → широта, довгота) для Open-Meteo
CITIES: dict[str, Tuple[float, float]] = {
    "Київ": (50.45, 30.52),
    "Вінниця": (49.23, 28.47),
    "Дніпро": (48.46, 35.05),
    "Донецьк": (48.00, 37.80),
    "Житомир": (50.25, 28.66),
    "Запоріжжя": (47.84, 35.14),
    "Івано-Франківськ": (48.92, 24.71),
    "Кам'янське": (48.51, 34.60),
    "Кам'янець-Подільський": (48.68, 26.59),
    "Кременчук": (49.07, 33.42),
    "Кривий Ріг": (47.91, 33.39),
    "Кропивницький": (48.51, 32.26),
    "Луцьк": (50.75, 25.33),
    "Львів": (49.84, 24.03),
    "Миколаїв": (46.97, 31.99),
    "Одеса": (46.48, 30.73),
    "Полтава": (49.59, 34.55),
    "Рівне": (50.62, 26.25),
    "Суми": (50.92, 34.80),
    "Тернопіль": (49.55, 25.59),
    "Ужгород": (48.62, 22.30),
    "Умань": (48.75, 30.22),
    "Харків": (49.99, 36.23),
    "Херсон": (46.64, 32.62),
    "Хмельницький": (49.42, 27.00),
    "Черкаси": (49.44, 32.06),
    "Чернівці": (48.29, 25.94),
    "Чернігів": (51.50, 31.29),
    "Біла Церква": (49.80, 30.12),
    "Маріуполь": (47.10, 37.55),
    "Мелітополь": (46.85, 35.37),
    "Бердянськ": (46.75, 36.79),
    "Відень": (48.21, 16.37),
    "Баден": (48.01, 16.23),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_city(lat: float, lon: float) -> str:
    """Найближче місто з нашого списку за координатами."""
    best_name = "Київ"
    best_dist = float("inf")
    for name, (clat, clon) in CITIES.items():
        dist = _haversine_km(lat, lon, clat, clon)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def detect_city_by_ip() -> Optional[str]:
    """
    Приблизне місцезнаходження за публічною IP-адресою (без GPS).
    Повертає назву міста зі списку CITIES або None.
    """
    try:
        with urllib.request.urlopen(
            "http://ip-api.com/json/?fields=status,lat,lon",
            timeout=6,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
        if data.get("status") != "success":
            return None
        lat = float(data["lat"])
        lon = float(data["lon"])
        return nearest_city(lat, lon)
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError):
        return None


_CACHE_TTL = timedelta(minutes=30)
_cache: Dict[str, Tuple[int, datetime]] = {}
_cache_lock = Lock()

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds


def _fetch_pressure_raw(lat: float, lon: float) -> Optional[int]:
    """Single HTTP attempt; returns mmHg value or None."""
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current=surface_pressure"
    )
    with urllib.request.urlopen(url, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    hpa = data.get("current", {}).get("surface_pressure")
    if hpa is None:
        return None
    return int(round(float(hpa) * 0.75006))


def fetch_atmospheric_pressure_mmhg(city: str = "Київ") -> Optional[int]:
    """Отримати поточний атмосферний тиск (мм рт. ст.) через Open-Meteo API.

    Результат кешується на 30 хв. При мережевих помилках виконується
    до 3 спроб з експоненційним відступом (1 с, 2 с, 4 с).
    """
    with _cache_lock:
        cached = _cache.get(city)
        if cached is not None:
            value, ts = cached
            if datetime.now() - ts < _CACHE_TTL:
                return value

    coords = CITIES.get(city, CITIES["Київ"])
    lat, lon = coords
    result: Optional[int] = None
    for attempt in range(_MAX_RETRIES):
        try:
            result = _fetch_pressure_raw(lat, lon)
            break
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError):
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_BASE_DELAY * (2 ** attempt))

    if result is not None:
        with _cache_lock:
            _cache[city] = (result, datetime.now())
    return result


def invalidate_weather_cache(city: Optional[str] = None) -> None:
    """Clear cached weather data for a city (or all cities if city is None)."""
    with _cache_lock:
        if city is None:
            _cache.clear()
        else:
            _cache.pop(city, None)


def city_names() -> list[str]:
    """Список міст для випадаючого списку (Київ першим, решта за алфавітом)."""
    names = sorted(CITIES.keys(), key=str.casefold)
    if "Київ" in names:
        names.remove("Київ")
        names.insert(0, "Київ")
    return names
