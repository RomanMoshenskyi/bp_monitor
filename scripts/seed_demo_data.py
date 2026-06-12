"""Seed realistic BP measurement data for demo patients."""
from __future__ import annotations

import os, sys, random, uuid
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "bp_monitor")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "admin")

from app.database import db_cursor

MOODS = ["Спокійний", "Робочий день", "Стрес", "Відпочинок"]
ACTIVITIES = ["Низька", "Середня", "Висока"]

PATIENTS = [
    {
        "id": 3,
        "name": "Пацієнт Демо",
        # Hypertensive patient — elevated baseline, improving over time
        "sys_base": 155, "dia_base": 95, "pulse_base": 82,
        "sys_trend": -0.10,   # gradual improvement over 90 days
        "noise_sys": 14, "noise_dia": 9, "noise_pulse": 10,
    },
    {
        "id": 5,
        "name": "Test",
        # Young healthy patient — normal range, slight morning spikes
        "sys_base": 122, "dia_base": 78, "pulse_base": 70,
        "sys_trend": 0.0,
        "noise_sys": 10, "noise_dia": 7, "noise_pulse": 8,
    },
]

DAYS = 90
READINGS_PER_DAY = 2   # morning + evening

rng = random.Random(42)

def gen_pressure(base: float, trend_per_day: float, day: int, noise: int) -> int:
    val = base + trend_per_day * day + rng.gauss(0, noise)
    return max(70, min(220, round(val)))

def seed_patient(patient: dict) -> int:
    pid = patient["id"]
    now = datetime.now()
    start = now - timedelta(days=DAYS - 1)

    # Delete existing test measurements to avoid dupes
    with db_cursor() as cur:
        cur.execute("DELETE FROM measurements WHERE user_id = %s", (pid,))

    count = 0
    for day_offset in range(DAYS):
        day_dt = start + timedelta(days=day_offset)

        for reading in range(READINGS_PER_DAY):
            # Morning ~ 07:00-08:30, Evening ~ 20:00-21:30
            if reading == 0:
                hour = rng.randint(7, 8)
                minute = rng.randint(0, 59)
            else:
                hour = rng.randint(20, 21)
                minute = rng.randint(0, 59)

            ts = day_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)

            sys_val = gen_pressure(patient["sys_base"], patient["sys_trend"], day_offset, patient["noise_sys"])
            dia_val = gen_pressure(patient["dia_base"], patient["sys_trend"] * 0.6, day_offset, patient["noise_dia"])
            pulse   = gen_pressure(patient["pulse_base"], 0, 0, patient["noise_pulse"])
            # keep diastolic < systolic
            dia_val = min(dia_val, sys_val - 20)

            mood     = rng.choice(MOODS)
            activity = rng.choice(ACTIVITIES)
            # slightly elevated BP on stress days
            if mood == "Стрес":
                sys_val = min(220, sys_val + rng.randint(5, 15))
            med_taken = rng.random() < 0.55
            atm_press = rng.randint(740, 775)
            notes = ""
            if rng.random() < 0.12:
                notes = rng.choice([
                    "Голова болить вранці",
                    "Відчуваю втому",
                    "Після прогулянки",
                    "Після кави",
                    "Спокійний день",
                    "Після тренування",
                ])

            mid = str(uuid.uuid4())
            with db_cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO measurements (
                        id, user_id, timestamp, systolic, diastolic, pulse,
                        mood, notes, atmospheric_pressure,
                        medication_taken, activity_level
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (mid, pid, ts, sys_val, dia_val, pulse,
                     mood, notes, atm_press, med_taken, activity),
                )
            count += 1

    return count


if __name__ == "__main__":
    for p in PATIENTS:
        n = seed_patient(p)
        print(f"  ✅  {p['name']} (id={p['id']}): {n} вимірювань додано")
    print("\nГотово!")
