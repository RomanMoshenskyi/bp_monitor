#!/usr/bin/env python3
"""
Seed demo data: 10 doctors + 12 patients with rich historical records.

Each patient gets:
  - 50–90 BP measurements spread over 90 days (morning/afternoon/evening/night)
  - 2–4 completed prescription courses with medication_intakes
  - 1–2 active prescriptions
  - 2–5 doctor recommendations
  - 1–3 doctor reports (signed)
  - Doctor-patient assignments

Run:
    python seed_demo_data.py
"""
import os, sys, random, hashlib, secrets, uuid
from datetime import datetime, date, timedelta, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import psycopg2

# ── DB config ────────────────────────────────────────────────────────────────
DB = dict(host="localhost", port=5432, dbname="bp_monitor",
          user="postgres", password="1234")

# ── Helpers ───────────────────────────────────────────────────────────────────
def _hash(pw: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000)
    return f"{salt}${digest.hex()}"

rng = random.Random(42)

def jitter(val, lo, hi):
    return max(lo, min(hi, val + rng.randint(-8, 8)))

# ── Data definitions ──────────────────────────────────────────────────────────
DOCTORS = [
    ("dr_kovalenko",  "Коваленко Олег Іванович",     "Кардіолог",      "Кардіологія"),
    ("dr_shevchenko", "Шевченко Марія Петрівна",     "Терапевт",       "Терапія"),
    ("dr_bondar",     "Бондар Сергій Миколайович",   "Невролог",       "Неврологія"),
    ("dr_lysenko",    "Лисенко Ірина Василівна",     "Ендокринолог",   "Ендокринологія"),
    ("dr_moroz",      "Мороз Андрій Олексійович",    "Кардіолог",      "Кардіологія"),
    ("dr_hrytsenko",  "Гриценко Наталія Сергіївна",  "Терапевт",       "Терапія"),
    ("dr_petrenko",   "Петренко Дмитро Юрійович",    "Пульмонолог",    "Пульмонологія"),
    ("dr_savchenko",  "Савченко Олена Борисівна",    "Ревматолог",     "Ревматологія"),
    ("dr_tkachenko",  "Ткаченко Василь Андрійович",  "Уролог",         "Урологія"),
    ("dr_kravchenko", "Кравченко Людмила Іванівна",  "Офтальмолог",    "Офтальмологія"),
]

PATIENTS = [
    ("p_bondarenko",  "Бондаренко Іван Степанович",   55, True),
    ("p_kovalchuk",   "Ковальчук Оксана Михайлівна",  48, False),
    ("p_melnyk",      "Мельник Григорій Павлович",    62, True),
    ("p_shvets",      "Швець Тетяна Олексіївна",      45, False),
    ("p_karpenko",    "Карпенко Микола Іванович",     70, True),
    ("p_boyko",       "Бойко Ганна Василівна",         52, False),
    ("p_marchenko",   "Марченко Олег Петрович",        38, True),
    ("p_sydorenko",   "Сидоренко Валентина Миколаївна",67, False),
    ("p_rudenko",     "Руденко Андрій Олексійович",   43, True),
    ("p_tkach",       "Ткач Людмила Сергіївна",        58, False),
    ("p_zhuk",        "Жук Віктор Борисович",          61, True),
    ("p_kovalenko2",  "Коваленко Наталія Іванівна",    49, False),
]

MEDICATIONS = [
    ("Лізиноприл",     "таблетки", "10 мг",  1),
    ("Амлодипін",      "таблетки", "5 мг",   1),
    ("Бісопролол",     "таблетки", "5 мг",   1),
    ("Лозартан",       "таблетки", "50 мг",  1),
    ("Периндоприл",    "таблетки", "4 мг",   1),
    ("Індапамід",      "таблетки", "2.5 мг", 1),
    ("Метопролол",     "таблетки", "25 мг",  2),
    ("Валсартан",      "таблетки", "80 мг",  1),
    ("Еналаприл",      "таблетки", "10 мг",  2),
    ("Телмісартан",    "таблетки", "40 мг",  1),
    ("Карведилол",     "таблетки", "12.5 мг",2),
    ("Фуросемід",      "таблетки", "40 мг",  1),
    ("Аспірин Кардіо", "таблетки", "100 мг", 1),
    ("Аторвастатин",   "таблетки", "20 мг",  1),
    ("Розувастатин",   "таблетки", "10 мг",  1),
]

COMPLAINTS = [
    "Скарги на головний біль, запаморочення, підвищений артеріальний тиск до {sys}/{dia} мм рт.ст.",
    "Відчуття важкості в потилиці, серцебиття, підвищення АТ до {sys}/{dia} мм рт.ст.",
    "Головний біль, шум у вухах, АТ {sys}/{dia} мм рт.ст. протягом 3 днів.",
    "Погане самопочуття вранці, підвищений тиск {sys}/{dia} мм рт.ст., слабкість.",
    "Задишка при навантаженні, підвищений АТ {sys}/{dia}/{pulse} мм рт.ст.",
]

DIAGNOSES = [
    ("Гіпертонічна хвороба II ст.", "I11.9"),
    ("Есенціальна гіпертензія",     "I10"),
    ("Гіпертонічна хвороба I ст.",  "I10"),
    ("Симптоматична артеріальна гіпертензія", "I15.9"),
    ("Гіпертонічна хвороба III ст., ризик 4", "I13.1"),
]

CONCLUSIONS = [
    "Стан відносно задовільний. Рекомендовано продовжити антигіпертензивну терапію.",
    "Компенсований стан на тлі медикаментозного лікування. Рекомендовано динамічне спостереження.",
    "Спостерігається позитивна динаміка на фоні лікування. Корекція терапії не потрібна.",
    "Необхідний контроль АТ двічі на добу. Рекомендовано обмеження солі до 5 г/добу.",
    "Стан стабільний. Продовжити призначену терапію, явка через 1 місяць.",
]

RECOMMENDATIONS_TEXT = [
    "Вимірювати артеріальний тиск двічі на добу — вранці та ввечері.",
    "Обмежити вживання кухонної солі до 5 г на добу.",
    "Уникати фізичних та емоційних навантажень.",
    "Дотримуватись дієти з обмеженням жирної їжі.",
    "Регулярно приймати призначені препарати без пропусків.",
    "Щоденні прогулянки на свіжому повітрі 30–40 хвилин.",
    "Контроль маси тіла, ІМТ не більше 25.",
    "Відмова від куріння та алкоголю.",
    "Контроль рівня холестерину раз на 3 місяці.",
    "Уникати переохолодження та різких змін температури.",
]

NOTE_VARIANTS = [
    "Стрес на роботі", "Погана погода", "Кава вранці", "Поганий сон",
    "Фізичне навантаження", "Перевтома", "Без скарг", "Солона їжа ввечері",
    None, None, None,  # більше пустих нотаток
]

# ── Time slots for measurements ───────────────────────────────────────────────
TIME_SLOTS = [
    (6, 7),    # ранок
    (8, 9),    # ранок
    (12, 13),  # день
    (14, 15),  # день
    (18, 19),  # вечір
    (20, 21),  # вечір
    (22, 23),  # ніч
    (2, 3),    # глибока ніч (рідко)
]

def random_measurement_time(day_offset: int) -> datetime:
    base = datetime.utcnow() - timedelta(days=90) + timedelta(days=day_offset)
    slot = rng.choice(TIME_SLOTS[:7] if rng.random() < 0.9 else TIME_SLOTS)
    h = rng.randint(slot[0], slot[1])
    m = rng.randint(0, 59)
    return base.replace(hour=h, minute=m, second=rng.randint(0, 59), microsecond=0)

def patient_bp(age: int, hypertensive: bool):
    if hypertensive:
        sys_base = rng.randint(138, 168)
        dia_base = rng.randint(88, 104)
    else:
        sys_base = rng.randint(118, 140)
        dia_base = rng.randint(75, 92)
    age_bonus = (age - 40) // 10
    sys_base += age_bonus * 3
    dia_base += age_bonus
    pulse = rng.randint(62, 92)
    return sys_base, dia_base, pulse

def default_intake_times(freq: int):
    if freq == 1:   return [time(9, 0)]
    if freq == 2:   return [time(8, 0), time(20, 0)]
    if freq == 3:   return [time(8, 0), time(14, 0), time(20, 0)]
    return [time(8, 0), time(12, 0), time(16, 0), time(20, 0)]


# ── Main seeder ───────────────────────────────────────────────────────────────
def seed():
    conn = psycopg2.connect(**DB)
    conn.autocommit = False
    cur = conn.cursor()

    # ── Check if already seeded ──────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM users WHERE role IN ('doctor','patient')")
    if cur.fetchone()[0] >= 5:
        print("ℹ️  Demo data already present (≥5 users found). Skipping seed.")
        cur.close(); conn.close(); return

    print("🌱 Seeding demo data...")

    # ── Insert doctors ────────────────────────────────────────────────────────
    doctor_ids = []
    for username, full_name, position, spec in DOCTORS:
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, role, is_active,
                               specialization, email)
            VALUES (%s,%s,%s,'doctor',TRUE,%s,%s)
            ON CONFLICT (username) DO UPDATE SET full_name=EXCLUDED.full_name
            RETURNING id
        """, (username, _hash("DoctorPass123"), full_name, spec,
              f"{username}@clinic.ua"))
        doctor_ids.append(cur.fetchone()[0])
    print(f"   ✅ {len(doctor_ids)} doctors inserted")

    # ── Insert patients ───────────────────────────────────────────────────────
    patient_ids = []
    patient_meta = []  # (id, age, hypertensive)
    for username, full_name, age, hyper in PATIENTS:
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, role, age,
                               is_active, email)
            VALUES (%s,%s,%s,'patient',%s,TRUE,%s)
            ON CONFLICT (username) DO UPDATE SET full_name=EXCLUDED.full_name
            RETURNING id
        """, (username, _hash("PatientPass123"), full_name, age,
              f"{username}@mail.ua"))
        pid = cur.fetchone()[0]
        patient_ids.append(pid)
        patient_meta.append((pid, age, hyper))
    print(f"   ✅ {len(patient_ids)} patients inserted")

    # ── Assign each patient to 1–3 doctors ───────────────────────────────────
    for pid, age, hyper in patient_meta:
        assigned = rng.sample(doctor_ids, rng.randint(1, 3))
        for did in assigned:
            cur.execute("""
                INSERT INTO doctor_patient_assignments (doctor_id, patient_id)
                VALUES (%s,%s) ON CONFLICT DO NOTHING
            """, (did, pid))

    # ── Per-patient data ──────────────────────────────────────────────────────
    total_meas = 0
    total_presc = 0
    total_intakes = 0
    total_reports = 0
    total_recs = 0

    for pid, age, hyper in patient_meta:
        sys_base, dia_base, pulse_base = patient_bp(age, hyper)

        # ── Doctor assigned to this patient ──────────────────────────────────
        cur.execute("""
            SELECT doctor_id FROM doctor_patient_assignments
            WHERE patient_id=%s LIMIT 1
        """, (pid,))
        row = cur.fetchone()
        primary_doc = row[0] if row else rng.choice(doctor_ids)

        # ── BP Measurements (50–90 per patient) ──────────────────────────────
        n_meas = rng.randint(50, 90)
        meas_days = sorted(rng.sample(range(0, 90), min(n_meas, 90)))
        # fill remaining from duplicated days
        while len(meas_days) < n_meas:
            meas_days.append(rng.randint(0, 89))
        meas_days.sort()

        for day in meas_days:
            ts = random_measurement_time(day)
            sys_v = jitter(sys_base, 95, 195)
            dia_v = jitter(dia_base, 55, 120)
            pulse_v = jitter(pulse_base, 55, 105)
            note = rng.choice(NOTE_VARIANTS)
            atm_pressure = rng.randint(740, 775)
            mid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO measurements
                    (id, measured_at, systolic, diastolic, pulse, notes, atmospheric_pressure, user_id, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (mid, ts, sys_v, dia_v, pulse_v, note, atm_pressure, pid, ts))
        total_meas += n_meas

        # ── Completed prescription courses (2–4) ─────────────────────────────
        n_completed = rng.randint(2, 4)
        for i in range(n_completed):
            med = rng.choice(MEDICATIONS)
            med_name, med_form, dosage, freq = med
            duration = rng.choice([14, 21, 30])
            # completed in the past
            end_offset = rng.randint(10, 80)
            end_d = date.today() - timedelta(days=end_offset)
            start_d = end_d - timedelta(days=duration)
            rx_num = f"RX-{start_d.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            cur.execute("""
                INSERT INTO prescriptions
                    (doctor_id, patient_id, prescription_number, prescription_date,
                     medication_name, medication_form, dosage, frequency_per_day,
                     duration_days, start_date, end_date, status,
                     patient_notified, notification_accepted,
                     prescribed_for, take_with_food)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'completed',TRUE,TRUE,%s,%s)
                RETURNING id
            """, (primary_doc, pid, rx_num, start_d,
                  med_name, med_form, dosage, freq,
                  duration, start_d, end_d,
                  "Лікування артеріальної гіпертензії",
                  rng.choice([True, False])))
            presc_id = cur.fetchone()[0]
            total_presc += 1

            # Generate intake records for completed course
            times = default_intake_times(freq)
            cur_day = start_d
            while cur_day <= end_d:
                for t in times:
                    sched = datetime.combine(cur_day, t)
                    # 85–95% taken, rest missed/skipped
                    roll = rng.random()
                    if roll < 0.88:
                        status = "taken"
                        taken_at = sched + timedelta(minutes=rng.randint(-10, 30))
                        on_time = True
                        delay = 0
                    elif roll < 0.93:
                        status = "late"
                        taken_at = sched + timedelta(minutes=rng.randint(61, 180))
                        on_time = False
                        delay = rng.randint(61, 180)
                    elif roll < 0.97:
                        status = "missed"
                        taken_at = None
                        on_time = False
                        delay = None
                    else:
                        status = "skipped"
                        taken_at = None
                        on_time = False
                        delay = None
                    cur.execute("""
                        INSERT INTO medication_intakes
                            (prescription_id, patient_id, scheduled_time, taken_at,
                             status, taken_on_time, minutes_delay)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (presc_id, pid, sched, taken_at, status, on_time, delay))
                    total_intakes += 1
                cur_day += timedelta(days=1)

        # ── Active prescriptions (1–2) ────────────────────────────────────────
        n_active = rng.randint(1, 2)
        for i in range(n_active):
            med = rng.choice(MEDICATIONS)
            med_name, med_form, dosage, freq = med
            duration = rng.choice([30, 60, 90])
            start_d = date.today() - timedelta(days=rng.randint(1, 20))
            end_d = start_d + timedelta(days=duration)
            rx_num = f"RX-{start_d.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            cur.execute("""
                INSERT INTO prescriptions
                    (doctor_id, patient_id, prescription_number, prescription_date,
                     medication_name, medication_form, dosage, frequency_per_day,
                     duration_days, start_date, end_date, status,
                     patient_notified, notification_accepted,
                     prescribed_for, take_with_food)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',TRUE,TRUE,%s,%s)
                RETURNING id
            """, (primary_doc, pid, rx_num, start_d,
                  med_name, med_form, dosage, freq,
                  duration, start_d, end_d,
                  "Тривала антигіпертензивна терапія",
                  rng.choice([True, False])))
            presc_id = cur.fetchone()[0]
            total_presc += 1

            # Intakes from start_d to yesterday
            times = default_intake_times(freq)
            cur_day = start_d
            yesterday = date.today() - timedelta(days=1)
            while cur_day <= yesterday:
                for t in times:
                    sched = datetime.combine(cur_day, t)
                    roll = rng.random()
                    if roll < 0.85:
                        status = "taken"
                        taken_at = sched + timedelta(minutes=rng.randint(-10, 25))
                        on_time = True; delay = 0
                    elif roll < 0.92:
                        status = "late"
                        taken_at = sched + timedelta(minutes=rng.randint(61, 120))
                        on_time = False; delay = rng.randint(61, 120)
                    else:
                        status = "missed"
                        taken_at = None; on_time = False; delay = None
                    cur.execute("""
                        INSERT INTO medication_intakes
                            (prescription_id, patient_id, scheduled_time, taken_at,
                             status, taken_on_time, minutes_delay)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (presc_id, pid, sched, taken_at, status, on_time, delay))
                    total_intakes += 1
                # Today: pending
                sched_today = datetime.combine(date.today(), times[0])
                cur.execute("""
                    INSERT INTO medication_intakes
                        (prescription_id, patient_id, scheduled_time, status)
                    VALUES (%s,%s,%s,'pending')
                """, (presc_id, pid, sched_today))
                total_intakes += 1
                cur_day += timedelta(days=1)

        # ── Doctor reports (1–3, signed) ──────────────────────────────────────
        n_reports = rng.randint(1, 3)
        doc_name_map = {}
        for uname, fname, pos, spec in DOCTORS:
            doc_name_map[uname] = (fname, pos, spec)

        for i in range(n_reports):
            report_date = date.today() - timedelta(days=rng.randint(5, 85))
            rn = f"MR-{report_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
            diag_name, diag_code = rng.choice(DIAGNOSES)
            sys_v = jitter(sys_base, 130, 185)
            dia_v = jitter(dia_base, 85, 115)
            complaint = rng.choice(COMPLAINTS).format(
                sys=sys_v, dia=dia_v, pulse=pulse_base)

            # Pick doctor for this report
            report_doc_id = primary_doc
            # find name for that doctor id
            cur.execute("SELECT username FROM users WHERE id=%s", (report_doc_id,))
            doc_uname = cur.fetchone()[0]
            doc_fname, doc_pos, doc_spec = doc_name_map.get(
                doc_uname, ("Лікар", "Лікар загальної практики", "Терапія"))

            cur.execute("""
                INSERT INTO doctor_reports
                    (patient_id, doctor_id, report_number, report_date,
                     chief_complaint, history_illness,
                     general_condition, consciousness, body_temperature,
                     heart_rate, respiratory_rate,
                     blood_pressure_sys, blood_pressure_dia,
                     heart_sounds, pulse_rhythm,
                     preliminary_diagnosis, final_diagnosis, diagnosis_code_icd,
                     treatment_plan, lifestyle_recommendations, diet_recommendations,
                     doctor_conclusion, next_visit_date,
                     doctor_signature_name, doctor_position, doctor_specialty,
                     signature_date, is_signed)
                VALUES (%s,%s,%s,%s,
                        %s,%s,
                        %s,%s,%s,
                        %s,%s,
                        %s,%s,
                        %s,%s,
                        %s,%s,%s,
                        %s,%s,%s,
                        %s,%s,
                        %s,%s,%s,
                        %s,%s)
                RETURNING id
            """, (
                pid, report_doc_id, rn, report_date,
                complaint,
                "Хворіє протягом кількох років. Приймає антигіпертензивні препарати.",
                "Задовільний", "Ясна", "36.6",
                pulse_base, rng.randint(16, 20),
                sys_v, dia_v,
                "Тони серця приглушені, ритмічні", "Ритмічний",
                diag_name, diag_name, diag_code,
                "Антигіпертензивна терапія, контроль АТ двічі на добу.",
                "Обмеження солі, фізична активність 30 хв/день.",
                "Дієта з обмеженням жирів та солі. Дієтичний стіл №10.",
                rng.choice(CONCLUSIONS),
                report_date + timedelta(days=rng.randint(28, 60)),
                doc_fname, doc_pos, doc_spec,
                datetime.combine(report_date, time(14, 0)), True,
            ))
            total_reports += 1

        # ── Doctor recommendations (2–5) ─────────────────────────────────────
        n_recs = rng.randint(2, 5)
        rec_texts = rng.sample(RECOMMENDATIONS_TEXT, n_recs)
        for rec_text in rec_texts:
            rec_date = datetime.utcnow() - timedelta(days=rng.randint(1, 60))
            cur.execute("""
                INSERT INTO doctor_recommendations
                    (patient_id, doctor_id, recommendation, created_at)
                VALUES (%s,%s,%s,%s)
            """, (pid, primary_doc, rec_text, rec_date))
            total_recs += 1

    conn.commit()
    print(f"   ✅ Measurements:       {total_meas}")
    print(f"   ✅ Prescriptions:      {total_presc}")
    print(f"   ✅ Medication intakes: {total_intakes}")
    print(f"   ✅ Doctor reports:     {total_reports}")
    print(f"   ✅ Recommendations:    {total_recs}")
    print("\n✅ Demo seed complete!")
    print("\n📋 Login credentials:")
    print("   Doctors:  dr_kovalenko … dr_kravchenko  /  DoctorPass123")
    print("   Patients: p_bondarenko … p_kovalenko2   /  PatientPass123")

    cur.close()
    conn.close()


if __name__ == "__main__":
    seed()
