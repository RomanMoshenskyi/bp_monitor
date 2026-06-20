-- BP Monitor - Complete Database Schema
-- Єдиний еталонний файл схеми. Ідемпотентний — безпечно запускати повторно.
-- Знятий з робочої БД pg_dump --schema-only, адаптований з IF NOT EXISTS.

SET client_encoding = 'UTF8';

-- ============================================================
-- FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

-- ============================================================
-- TABLE: users
-- ============================================================

CREATE TABLE IF NOT EXISTS public.users (
    id                   SERIAL PRIMARY KEY,
    username             VARCHAR(100)  NOT NULL,
    password_hash        VARCHAR(255)  NOT NULL,
    full_name            VARCHAR(255)  NOT NULL,
    role                 VARCHAR(20)   NOT NULL,
    age                  INTEGER,
    target_systolic      INTEGER       DEFAULT 120,
    target_diastolic     INTEGER       DEFAULT 80,
    target_pulse         INTEGER       DEFAULT 75,
    is_active            BOOLEAN       DEFAULT TRUE,
    email                VARCHAR(255),
    created_at           TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    deleted_at           TIMESTAMP,
    is_verified          BOOLEAN       DEFAULT FALSE,
    verification_token   VARCHAR(255),
    threshold_profile_id INTEGER,
    updated_at           TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    specialization       VARCHAR(100),
    primary_doctor_id    INTEGER,
    CONSTRAINT users_username_key   UNIQUE (username),
    CONSTRAINT users_email_key      UNIQUE (email),
    CONSTRAINT users_role_check     CHECK (role = ANY (ARRAY['patient','doctor','admin']))
);

CREATE INDEX IF NOT EXISTS idx_users_role     ON public.users (role);
CREATE INDEX IF NOT EXISTS idx_users_username ON public.users (username);
CREATE INDEX IF NOT EXISTS idx_users_active   ON public.users (username) WHERE deleted_at IS NULL;

-- ============================================================
-- TABLE: profile
-- ============================================================

CREATE TABLE IF NOT EXISTS public.profile (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(255) NOT NULL DEFAULT 'Користувач',
    age              INTEGER      NOT NULL DEFAULT 28,
    target_systolic  INTEGER      NOT NULL DEFAULT 120,
    target_diastolic INTEGER      NOT NULL DEFAULT 80,
    target_pulse     INTEGER      NOT NULL DEFAULT 75,
    created_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

DROP TRIGGER IF EXISTS update_profile_updated_at ON public.profile;
CREATE TRIGGER update_profile_updated_at
    BEFORE UPDATE ON public.profile
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

INSERT INTO public.profile (name, age, target_systolic, target_diastolic, target_pulse)
SELECT 'Користувач', 28, 120, 80, 75
WHERE NOT EXISTS (SELECT 1 FROM public.profile);

-- ============================================================
-- TABLE: system_thresholds
-- ============================================================

CREATE TABLE IF NOT EXISTS public.system_thresholds (
    id               SERIAL PRIMARY KEY,
    systolic_high    INTEGER   NOT NULL DEFAULT 140,
    diastolic_high   INTEGER   NOT NULL DEFAULT 90,
    systolic_low     INTEGER   NOT NULL DEFAULT 90,
    diastolic_low    INTEGER   NOT NULL DEFAULT 60,
    pulse_high       INTEGER   NOT NULL DEFAULT 100,
    pulse_low        INTEGER   NOT NULL DEFAULT 50,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by       INTEGER   REFERENCES public.users(id)
);

INSERT INTO public.system_thresholds
    (systolic_high, diastolic_high, systolic_low, diastolic_low, pulse_high, pulse_low)
SELECT 140, 90, 90, 60, 100, 50
WHERE NOT EXISTS (SELECT 1 FROM public.system_thresholds);

-- ============================================================
-- TABLE: measurements
-- ============================================================

CREATE TABLE IF NOT EXISTS public.measurements (
    id                   VARCHAR(50) PRIMARY KEY,
    measured_at          TIMESTAMP   NOT NULL,
    systolic             INTEGER     NOT NULL,
    diastolic            INTEGER     NOT NULL,
    pulse                INTEGER     NOT NULL,
    mood                 VARCHAR(100) DEFAULT 'Спокійний',
    notes                TEXT         DEFAULT '',
    atmospheric_pressure INTEGER,
    medication_taken     BOOLEAN      DEFAULT FALSE,
    activity_level       VARCHAR(50)  DEFAULT 'Низька',
    created_at           TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    user_id              INTEGER      REFERENCES public.users(id) ON DELETE CASCADE,
    deleted_at           TIMESTAMP,
    weather_snapshot_id  INTEGER,
    latitude             DOUBLE PRECISION,
    longitude            DOUBLE PRECISION,
    updated_at           TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON public.measurements (measured_at);
CREATE INDEX IF NOT EXISTS idx_measurements_user_id   ON public.measurements (user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_active    ON public.measurements (user_id, measured_at)
    WHERE deleted_at IS NULL;

-- ============================================================
-- TABLE: doctor_recommendations
-- ============================================================

CREATE TABLE IF NOT EXISTS public.doctor_recommendations (
    id             SERIAL PRIMARY KEY,
    patient_id     INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    doctor_id      INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    recommendation TEXT    NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_patient ON public.doctor_recommendations (patient_id);

-- ============================================================
-- TABLE: doctor_patient_assignments
-- ============================================================

CREATE TABLE IF NOT EXISTS public.doctor_patient_assignments (
    id          SERIAL PRIMARY KEY,
    doctor_id   INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    patient_id  INTEGER NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT doctor_patient_assignments_doctor_id_patient_id_key UNIQUE (doctor_id, patient_id)
);

CREATE INDEX IF NOT EXISTS idx_dpa_doctor  ON public.doctor_patient_assignments (doctor_id);
CREATE INDEX IF NOT EXISTS idx_dpa_patient ON public.doctor_patient_assignments (patient_id);

-- ============================================================
-- TABLE: prescriptions
-- ============================================================

CREATE TABLE IF NOT EXISTS public.prescriptions (
    id                    SERIAL PRIMARY KEY,
    doctor_id             INTEGER      NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    patient_id            INTEGER      NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    prescription_number   VARCHAR(50)  NOT NULL UNIQUE,
    prescription_date     DATE         NOT NULL DEFAULT CURRENT_DATE,
    medication_name       VARCHAR(200) NOT NULL,
    medication_form       VARCHAR(100),
    dosage                VARCHAR(100) NOT NULL,
    frequency_per_day     INTEGER      NOT NULL DEFAULT 1,
    specific_times        TIME[],
    duration_days         INTEGER,
    start_date            DATE         NOT NULL DEFAULT CURRENT_DATE,
    end_date              DATE,
    take_with_food        BOOLEAN,
    take_before_food      BOOLEAN,
    take_after_food       BOOLEAN,
    special_instructions  TEXT,
    prescribed_for        TEXT,
    contraindications     TEXT,
    side_effects_notes    TEXT,
    interactions_warning  TEXT,
    status                VARCHAR(20)  NOT NULL DEFAULT 'active',
    patient_notified      BOOLEAN      DEFAULT FALSE,
    notification_seen_at  TIMESTAMP,
    notification_accepted BOOLEAN,
    created_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    cancelled_at          TIMESTAMP,
    cancelled_reason      TEXT
);

CREATE INDEX IF NOT EXISTS idx_prescriptions_doctor_id        ON public.prescriptions (doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient_id       ON public.prescriptions (patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_status           ON public.prescriptions (status);
CREATE INDEX IF NOT EXISTS idx_prescriptions_prescription_date ON public.prescriptions (prescription_date);

DROP TRIGGER IF EXISTS update_prescriptions_updated_at ON public.prescriptions;
CREATE TRIGGER update_prescriptions_updated_at
    BEFORE UPDATE ON public.prescriptions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- TABLE: medications
-- ============================================================

CREATE TABLE IF NOT EXISTS public.medications (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    dosage          VARCHAR(50)  NOT NULL,
    unit            VARCHAR(20),
    prescription_id INTEGER      REFERENCES public.prescriptions(id) ON DELETE SET NULL,
    status          VARCHAR(20)  DEFAULT 'active',
    created_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_medications_prescription_id ON public.medications (prescription_id);

DROP TRIGGER IF EXISTS update_medications_updated_at ON public.medications;
CREATE TRIGGER update_medications_updated_at
    BEFORE UPDATE ON public.medications
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- TABLE: medication_intakes
-- ============================================================

CREATE TABLE IF NOT EXISTS public.medication_intakes (
    id                     SERIAL PRIMARY KEY,
    medication_id          INTEGER      REFERENCES public.medications(id) ON DELETE CASCADE,
    prescription_id        INTEGER      REFERENCES public.prescriptions(id) ON DELETE SET NULL,
    patient_id             INTEGER      NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    measurement_id         VARCHAR(50)  REFERENCES public.measurements(id) ON DELETE SET NULL,
    scheduled_time         TIMESTAMP    NOT NULL,
    taken_at               TIMESTAMP,
    dosage_taken           REAL,
    dosage_unit            VARCHAR(20),
    status                 VARCHAR(20)  NOT NULL DEFAULT 'pending',
    taken_on_time          BOOLEAN,
    minutes_delay          INTEGER,
    taken_with_food        BOOLEAN,
    notes                  TEXT,
    skip_reason            VARCHAR(200),
    reminder_sent          BOOLEAN      DEFAULT FALSE,
    reminder_sent_at       TIMESTAMP,
    reminder_acknowledged  BOOLEAN      DEFAULT FALSE,
    created_at             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_medication_intakes_patient_id      ON public.medication_intakes (patient_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_prescription_id ON public.medication_intakes (prescription_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_medication_id   ON public.medication_intakes (medication_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_scheduled_time  ON public.medication_intakes (scheduled_time);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_status          ON public.medication_intakes (status);

DROP TRIGGER IF EXISTS update_medication_intakes_updated_at ON public.medication_intakes;
CREATE TRIGGER update_medication_intakes_updated_at
    BEFORE UPDATE ON public.medication_intakes
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- TABLE: doctor_reports
-- ============================================================

CREATE TABLE IF NOT EXISTS public.doctor_reports (
    id                       SERIAL PRIMARY KEY,
    patient_id               INTEGER      NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    doctor_id                INTEGER      NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    report_number            VARCHAR(50)  NOT NULL UNIQUE,
    report_date              DATE         NOT NULL DEFAULT CURRENT_DATE,
    chief_complaint          TEXT,
    history_illness          TEXT,
    history_life             TEXT,
    objective_exam           TEXT,
    general_condition        VARCHAR(100),
    consciousness            VARCHAR(50),
    body_temperature         VARCHAR(10),
    skin_condition           VARCHAR(200),
    heart_rate               INTEGER,
    respiratory_rate         INTEGER,
    blood_pressure_sys       INTEGER,
    blood_pressure_dia       INTEGER,
    heart_sounds             VARCHAR(200),
    pulse_rhythm             VARCHAR(50),
    pulse_character          VARCHAR(100),
    preliminary_diagnosis    TEXT,
    final_diagnosis          TEXT,
    diagnosis_code_icd       VARCHAR(20),
    ecg_results              TEXT,
    xray_results             TEXT,
    lab_results              TEXT,
    other_exams              TEXT,
    treatment_plan           TEXT,
    prescriptions            TEXT,
    procedures               TEXT,
    lifestyle_recommendations TEXT,
    diet_recommendations     TEXT,
    activity_recommendations TEXT,
    doctor_conclusion        TEXT,
    prognosis                VARCHAR(200),
    next_visit_date          DATE,
    next_visit_reason        VARCHAR(300),
    sick_leave_required      BOOLEAN      DEFAULT FALSE,
    sick_leave_days          INTEGER,
    sick_leave_from          DATE,
    sick_leave_to            DATE,
    doctor_signature_name    VARCHAR(200),
    doctor_position          VARCHAR(200),
    doctor_specialty         VARCHAR(200),
    signature_date           TIMESTAMP,
    is_signed                BOOLEAN      DEFAULT FALSE,
    file_path                VARCHAR(500),
    file_size                INTEGER,
    created_at               TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_doctor_reports_doctor_id  ON public.doctor_reports (doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_reports_patient_id ON public.doctor_reports (patient_id);
CREATE INDEX IF NOT EXISTS idx_doctor_reports_report_date ON public.doctor_reports (report_date);

DROP TRIGGER IF EXISTS update_doctor_reports_updated_at ON public.doctor_reports;
CREATE TRIGGER update_doctor_reports_updated_at
    BEFORE UPDATE ON public.doctor_reports
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ============================================================
-- TABLE: audit_logs
-- ============================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER      NOT NULL REFERENCES public.users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id   INTEGER,
    details     TEXT,
    ip_address  VARCHAR(45),
    user_agent  VARCHAR(255),
    "timestamp" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_audit_logs_id        ON public.audit_logs (id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action    ON public.audit_logs (action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id   ON public.audit_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_timestamp ON public.audit_logs ("timestamp");
CREATE INDEX IF NOT EXISTS ix_audit_user_action    ON public.audit_logs (user_id, action);
CREATE INDEX IF NOT EXISTS ix_audit_user_timestamp ON public.audit_logs (user_id, "timestamp");
CREATE INDEX IF NOT EXISTS ix_audit_action_timestamp ON public.audit_logs (action, "timestamp");
