from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from math import sqrt
from typing import Iterable, List, Optional, Sequence

from .models import Measurement, measurement_to_row


DATE_FMT = "%Y-%m-%d %H:%M"


def parse_ts(value: str) -> datetime:
    return datetime.strptime(value, DATE_FMT)


def filter_by_days(measurements: Sequence[Measurement], days: int) -> List[Measurement]:
    if not measurements:
        return []
    latest = max(parse_ts(m.timestamp) for m in measurements)
    border = latest - timedelta(days=days)
    return [m for m in measurements if parse_ts(m.timestamp) >= border]


def average(values: Iterable[float]) -> float:
    data = list(values)
    return sum(data) / len(data) if data else 0.0


def latest_measurement(measurements: Sequence[Measurement]) -> Optional[Measurement]:
    if not measurements:
        return None
    return max(measurements, key=lambda m: parse_ts(m.timestamp))


def pressure_status(systolic: int, diastolic: int) -> str:
    if systolic < 90 or diastolic < 60:
        return "Знижений"
    if systolic >= 140 or diastolic >= 90:
        return "Гіпертензія II"
    if 130 <= systolic <= 139 or 80 <= diastolic <= 89:
        return "Гіпертензія I"
    if 120 <= systolic <= 129 and diastolic < 80:
        return "Підвищений"
    return "Норма"


def summary(measurements: Sequence[Measurement]) -> dict:
    if not measurements:
        return {
            "count": 0,
            "avg_systolic": 0,
            "avg_diastolic": 0,
            "avg_pulse": 0,
            "latest_status": "Немає даних",
            "avg_pressure": 0,
            "correlation": None,
            "pressure_trend": "Немає даних",
        }
    latest = latest_measurement(measurements)
    systolic_values = [m.systolic for m in measurements]
    diastolic_values = [m.diastolic for m in measurements]
    pulse_values = [m.pulse for m in measurements]
    atmos = [m.atmospheric_pressure for m in measurements if m.atmospheric_pressure is not None]
    avg_sys = average(systolic_values)
    avg_dia = average(diastolic_values)
    trend = "Стабільний"
    if len(systolic_values) >= 2:
        if systolic_values[-1] - systolic_values[0] > 6:
            trend = "До зростання"
        elif systolic_values[0] - systolic_values[-1] > 6:
            trend = "До зниження"
    return {
        "count": len(measurements),
        "avg_systolic": round(avg_sys, 1),
        "avg_diastolic": round(avg_dia, 1),
        "avg_pulse": round(average(pulse_values), 1),
        "latest_status": pressure_status(latest.systolic, latest.diastolic) if latest else "Немає даних",
        "avg_pressure": round(average(atmos), 1) if atmos else 0,
        "correlation": round(correlation_atmospheric(measurements), 3) if correlation_atmospheric(measurements) is not None else None,
        "pressure_trend": trend,
    }


def correlation_atmospheric(measurements: Sequence[Measurement]) -> Optional[float]:
    pairs = [(m.atmospheric_pressure, m.systolic) for m in measurements if m.atmospheric_pressure is not None]
    if len(pairs) < 3:
        return None
    xs = [float(x) for x, _ in pairs]
    ys = [float(y) for _, y in pairs]
    mean_x = average(xs)
    mean_y = average(ys)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = sqrt(sum((y - mean_y) ** 2 for y in ys))
    if denom_x == 0 or denom_y == 0:
        return None
    return numerator / (denom_x * denom_y)


def generate_recommendations(measurements: Sequence[Measurement]) -> List[str]:
    recs: List[str] = []
    if not measurements:
        return [
            "Додайте перше вимірювання для формування аналітики.",
            "Фіксуйте тиск в один і той самий час для коректного порівняння.",
            "Поле атмосферного тиску є опційним і використовується лише для додаткового аналізу.",
        ]

    latest = latest_measurement(measurements)
    last7 = filter_by_days(measurements, 7)
    stats = summary(last7)

    if latest and (latest.systolic >= 140 or latest.diastolic >= 90):
        recs.append("Останній запис свідчить про підвищені значення тиску. Доцільно повторити вимірювання у стані спокою та за потреби звернутися до лікаря.")
    elif latest and (latest.systolic < 95 or latest.diastolic < 60):
        recs.append("Зафіксовано знижені значення тиску. Варто контролювати самопочуття та уникати різкого фізичного навантаження.")
    else:
        recs.append("Поточні показники перебувають у прийнятному діапазоні. Рекомендується продовжувати регулярний моніторинг.")

    if stats["avg_pulse"] > 85:
        recs.append("Середній пульс за останні 7 днів підвищений. Бажано оцінювати вимірювання після 5–10 хвилин відпочинку.")

    corr = stats["correlation"]
    if corr is not None:
        if abs(corr) >= 0.55:
            recs.append("Виявлено помітний статистичний зв’язок між систолічним і атмосферним тиском. Це не є медичним висновком, але може бути корисним для індивідуального спостереження.")
        else:
            recs.append("Суттєвого зв’язку з атмосферним тиском не виявлено. Погодні дані варто трактувати як допоміжний фактор, а не причину змін.")
    else:
        recs.append("Для аналізу співставлення з атмосферним тиском бажано мати щонайменше 3–5 записів із заповненим полем атмосферного тиску.")

    if stats["pressure_trend"] == "До зростання":
        recs.append("Спостерігається тенденція до зростання систолічного тиску. Доцільно посилити контроль у найближчі дні.")

    return recs[:4]


