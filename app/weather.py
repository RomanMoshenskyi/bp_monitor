from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Optional, Tuple

# Координати міст України (назва  широта, довгота) для Open-Meteo
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
    "Бровари": (50.51, 30.80),
    "Буча": (50.55, 30.20),
    "Васильків": (50.37, 30.32),
    "Ірпінь": (50.52, 30.25),
    "Обухів": (50.12, 30.85),
    "Фастів": (50.08, 29.92),
    "Бориспіль": (50.35, 30.95),
    "Ніжин": (51.05, 31.88),
    "Прилуки": (50.59, 32.38),
    "Бахмач": (51.18, 33.00),
    "Конотоп": (51.23, 33.22),
    "Шостка": (51.87, 33.87),
    "Глухів": (51.66, 33.92),
    "Острог": (50.33, 26.52),
    "Дубно": (50.42, 25.73),
    "Ковель": (51.22, 24.71),
    "Нововолинськ": (50.73, 24.15),
    "Сарни": (51.33, 26.23),
    "Костопіль": (50.88, 26.25),
    "Млинів": (50.58, 25.97),
    "Здолбунів": (50.38, 26.22),
    "Славута": (50.30, 26.87),
    "Нетішин": (50.35, 26.62),
    "Шепетівка": (50.18, 27.06),
    "Ізяслав": (50.12, 26.82),
    "Старокостянтинів": (49.95, 27.00),
    "Кам'янець-Подільський": (48.68, 26.59),
    "Хотин": (48.50, 26.50),
    "Сторожинець": (48.15, 25.67),
    "Вижниця": (48.08, 25.38),
    "Кіцмань": (48.45, 25.33),
    "Новодністровськ": (48.35, 27.52),
    "Сокиряни": (48.17, 27.38),
    "Герца": (48.30, 26.08),
    "Тернопіль": (49.55, 25.59),
    "Чортків": (49.03, 25.78),
    "Бучач": (49.13, 25.40),
    "Копичинці": (49.03, 25.93),
    "Борщів": (48.80, 26.03),
    "Заліщики": (48.60, 25.78),
    "Кременець": (50.08, 25.72),
    "Ланівці": (49.88, 25.95),
    "Шумськ": (50.18, 25.92),
    "Івано-Франківськ": (48.92, 24.71),
    "Калуш": (48.95, 24.38),
    "Коломия": (48.53, 24.75),
    "Яремче": (48.45, 24.55),
    "Надвірна": (48.62, 24.58),
    "Долина": (48.93, 23.92),
    "Снятин": (48.45, 25.58),
    "Косів": (48.30, 25.08),
    "Ворохта": (48.27, 24.48),
    "Яворів": (49.95, 23.62),
    "Мостиська": (49.82, 23.33),
    "Самбір": (49.52, 23.42),
    "Дрогобич": (49.35, 23.50),
    "Стрий": (49.25, 23.58),
    "Сколе": (49.30, 23.48),
    "Мукачево": (48.45, 22.72),
    "Берегово": (48.28, 22.65),
    "Ужгород": (48.62, 22.30),
    "Чоп": (48.43, 22.17),
    "Перечин": (48.78, 22.52),
    "Свалява": (48.55, 23.05),
    "Вишково": (48.50, 23.40),
    "Іршава": (48.33, 23.42),
    "Хуст": (48.18, 23.30),
    "Тячів": (48.15, 23.58),
    "Рахів": (48.05, 24.22),
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
