"""
Наповнення БД демо-даними: пацієнти, вимірювання, рекомендації лікаря.
Запуск: python scripts/seed_patients.py
"""
from __future__ import annotations

import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.auth import ROLE_PATIENT, _hash_password  # noqa: E402
from app.database import connect, db_cursor  # noqa: E402
from app.migrations import run_migrations  # noqa: E402

PATIENTS = [
    {
        "username": "patient",
        "password": "PatientPass123",
        "full_name": "Коваленко Олена Петрівна",
        "age": 45,
        "target_systolic": 125,
        "target_diastolic": 82,
        "target_pulse": 72,
    },
    {
        "username": "petrenko_m",
        "password": "PatientPass123",
        "full_name": "Петренко Михайло Іванович",
        "age": 58,
        "target_systolic": 130,
        "target_diastolic": 85,
        "target_pulse": 70,
    },
    {
        "username": "sidorenko_a",
        "password": "PatientPass123",
        "full_name": "Сидоренко Анна Василівна",
        "age": 34,
        "target_systolic": 118,
        "target_diastolic": 78,
        "target_pulse": 68,
    },
    {
        "username": "melnyk_v",
        "password": "PatientPass123",
        "full_name": "Мельник Віктор Олегович",
        "age": 62,
        "target_systolic": 135,
        "target_diastolic": 88,
        "target_pulse": 74,
    },
    {
        "username": "bondar_i",
        "password": "PatientPass123",
        "full_name": "Бондар Ірина Степанівна",
        "age": 41,
        "target_systolic": 120,
        "target_diastolic": 80,
        "target_pulse": 76,
    },
    {
        "username": "savchenko_p",
        "password": "PatientPass123",
        "full_name": "Савченко Павло Миколайович",
        "age": 52,
        "target_systolic": 128,
        "target_diastolic": 84,
        "target_pulse": 71,
    },
]

MOODS = ["Спокійний", "Робочий день", "Стрес", "Після тренування", "Незадовільне самопочуття"]
ACTIVITIES = ["Низька", "Середня", "Висока"]
NOTES_SAMPLES = [
    "Після сну, натще",
    "Після сніданку",
    "Вечірнє вимірювання",
    "Після прогулянки",
    "Напружений робочий день",
    "Нормальне самопочуття",
    "Легкий головний біль",
    "Після прийому ліків",
    "",
]

DOCTOR_RECOMMENDATIONS = [
    "Рекомендую щоденний контроль тиску вранці та ввечері. Уникайте надмірної солі в раціоні.",
    "Спостерігається тенденція до підвищення систолічного тиску. Доцільно проконсультуватися з кардіологом.",
    "Показники стабільні. Продовжуйте поточний режим та фізичну активність помірної інтенсивності.",
    "Зафіксовано підвищений пульс — вимірюйте тиск після 10 хвилин спокою.",
    "Рекомендую вести щоденник вимірювань і відмічати прийом ліків у застосунку.",
]


def _ensure_patient(cur, data: dict) -> int:
    cur.execute("SELECT id FROM users WHERE username = %s", (data["username"],))
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE users
            SET full_name = %s, age = %s,
                target_systolic = %s, target_diastolic = %s, target_pulse = %s
            WHERE id = %s
            """,
            (
                data["full_name"],
                data["age"],
                data["target_systolic"],
                data["target_diastolic"],
                data["target_pulse"],
                row[0],
            ),
        )
        return row[0]
    cur.execute(
        """
        INSERT INTO users (
            username, password_hash, full_name, role, age,
            target_systolic, target_diastolic, target_pulse
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            data["username"],
            _hash_password(data["password"]),
            data["full_name"],
            ROLE_PATIENT,
            data["age"],
            data["target_systolic"],
            data["target_diastolic"],
            data["target_pulse"],
        ),
    )
    return cur.fetchone()[0]


def _generate_measurements(patient_id: int, profile: dict, count: int = 24) -> int:
    """Генерує вимірювання за останні ~30 днів."""
    base_sys = profile["target_systolic"]
    base_dia = profile["target_diastolic"]
    base_pulse = profile["target_pulse"]
    inserted = 0
    now = datetime.now()

    with db_cursor() as cur:
        for i in range(count):
            days_ago = random.randint(0, 28)
            hour = random.choice([7, 8, 9, 12, 18, 19, 21])
            minute = random.choice([0, 10, 20, 30, 45])
            ts = (now - timedelta(days=days_ago)).replace(
                hour=hour, minute=minute, second=0, microsecond=0
            )

            # Варіація навколо цільових показників
            stress = random.random()
            if stress > 0.85:
                systolic = base_sys + random.randint(12, 28)
                diastolic = base_dia + random.randint(8, 18)
            elif stress < 0.15:
                systolic = base_sys - random.randint(5, 15)
                diastolic = base_dia - random.randint(3, 10)
            else:
                systolic = base_sys + random.randint(-8, 10)
                diastolic = base_dia + random.randint(-5, 8)

            systolic = max(95, min(180, systolic))
            diastolic = max(55, min(115, diastolic))
            if systolic <= diastolic:
                systolic = diastolic + random.randint(25, 45)

            pulse = base_pulse + random.randint(-12, 18)
            pulse = max(55, min(105, pulse))
            atm = random.randint(735, 755)
            mid = uuid.uuid4().hex[:10]

            cur.execute("SELECT 1 FROM measurements WHERE id = %s", (mid,))
            if cur.fetchone():
                continue

            cur.execute(
                """
                INSERT INTO measurements (
                    id, user_id, timestamp, systolic, diastolic, pulse,
                    mood, notes, atmospheric_pressure, medication_taken, activity_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    mid,
                    patient_id,
                    ts,
                    systolic,
                    diastolic,
                    pulse,
                    random.choice(MOODS),
                    random.choice(NOTES_SAMPLES),
                    atm,
                    random.random() < 0.25,
                    random.choice(ACTIVITIES),
                ),
            )
            inserted += 1
    return inserted


def _seed_recommendations(patient_ids: list[int], doctor_id: int) -> int:
    count = 0
    with db_cursor() as cur:
        for pid in patient_ids:
            cur.execute(
                "SELECT COUNT(*) FROM doctor_recommendations WHERE patient_id = %s",
                (pid,),
            )
            if cur.fetchone()[0] >= 2:
                continue
            for text in random.sample(DOCTOR_RECOMMENDATIONS, k=min(2, len(DOCTOR_RECOMMENDATIONS))):
                cur.execute(
                    """
                    INSERT INTO doctor_recommendations (patient_id, doctor_id, recommendation)
                    VALUES (%s, %s, %s)
                    """,
                    (pid, doctor_id, text),
                )
                count += 1
    return count


def main() -> None:
    print("Міграції...")
    run_migrations()

    patient_ids: list[int] = []
    total_measurements = 0

    with db_cursor() as cur:
        for pdata in PATIENTS:
            pid = _ensure_patient(cur, pdata)
            patient_ids.append(pid)
            print(f"  Пацієнт: {pdata['full_name']} (id={pid}, логін: {pdata['username']})")

        cur.execute("SELECT id FROM users WHERE username = 'doctor' LIMIT 1")
        doctor_row = cur.fetchone()
        doctor_id = doctor_row[0] if doctor_row else None

    for pdata in PATIENTS:
        with db_cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (pdata["username"],))
            pid = cur.fetchone()[0]
        n = _generate_measurements(pid, pdata, count=random.randint(22, 30))
        total_measurements += n
        print(f"  + {n} вимірювань для {pdata['username']}")

    rec_count = 0
    if doctor_id and patient_ids:
        rec_count = _seed_recommendations(patient_ids, doctor_id)
        print(f"  + {rec_count} рекомендацій лікаря")

    print()
    print("Готово!")
    print(f"  Пацієнтів: {len(PATIENTS)}")
    print(f"  Вимірювань додано: {total_measurements}")
    print(f"  Пароль усіх нових пацієнтів: PatientPass123")
    print()
    print("Логіни: patient, petrenko_m, sidorenko_a, melnyk_v, bondar_i, savchenko_p")


if __name__ == "__main__":
    main()
