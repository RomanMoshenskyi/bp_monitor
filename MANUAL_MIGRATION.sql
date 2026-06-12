-- Manual Migration - BP Monitor Schema
-- Run this in pgAdmin Query Tool

-- ===========================================
-- MIGRATION 001: Initial 3 Core Tables
-- ===========================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'patient' CHECK (role IN ('patient', 'doctor', 'admin')),
    is_verified BOOLEAN DEFAULT FALSE,
    specialization VARCHAR(100),
    primary_doctor_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Weather snapshots table
CREATE TABLE IF NOT EXISTS weather_snapshots (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    pressure_hpa FLOAT,
    pressure_mmhg INTEGER,
    temperature FLOAT,
    humidity INTEGER,
    weather_description VARCHAR(255),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Measurements table
CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    systolic INTEGER NOT NULL CHECK (systolic > 0 AND systolic < 300),
    diastolic INTEGER NOT NULL CHECK (diastolic > 0 AND diastolic < 200),
    pulse INTEGER CHECK (pulse > 0 AND pulse < 300),
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude FLOAT,
    longitude FLOAT,
    notes TEXT,
    weather_snapshot_id INTEGER REFERENCES weather_snapshots(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON measurements(user_id);
CREATE INDEX IF NOT EXISTS idx_measurements_measured_at ON measurements(measured_at);
CREATE INDEX IF NOT EXISTS idx_weather_city_recorded ON weather_snapshots(city, recorded_at);

-- ===========================================
-- MIGRATION 002: All 11 Tables
-- ===========================================

-- Enum types
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('patient', 'doctor', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE activity_type AS ENUM ('walking', 'running', 'cycling', 'swimming', 'gym', 'yoga', 'sport', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE report_format AS ENUM ('pdf', 'csv', 'json');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE report_status AS ENUM ('pending', 'generating', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Medications table
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50),
    unit VARCHAR(20),
    frequency VARCHAR(50),
    notes TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medication intakes table
CREATE TABLE IF NOT EXISTS medication_intakes (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    measurement_id INTEGER REFERENCES measurements(id) ON DELETE SET NULL,
    taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Activity events table
CREATE TABLE IF NOT EXISTS activity_events (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measurement_id INTEGER REFERENCES measurements(id) ON DELETE SET NULL,
    activity_type VARCHAR(20) NOT NULL,
    duration_minutes INTEGER NOT NULL,
    intensity VARCHAR(10),
    calories_burned INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Threshold profiles table
CREATE TABLE IF NOT EXISTS threshold_profiles (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sys_min INTEGER DEFAULT 90,
    sys_max INTEGER DEFAULT 140,
    dia_min INTEGER DEFAULT 60,
    dia_max INTEGER DEFAULT 90,
    pulse_min INTEGER DEFAULT 50,
    pulse_max INTEGER DEFAULT 100,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily summaries table
CREATE TABLE IF NOT EXISTS daily_summaries (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    summary_date DATE NOT NULL UNIQUE,
    avg_systolic FLOAT,
    avg_diastolic FLOAT,
    avg_pulse FLOAT,
    measurement_count INTEGER DEFAULT 0,
    min_pressure_mmhg INTEGER,
    max_pressure_mmhg INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations table
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measurement_id INTEGER REFERENCES measurements(id) ON DELETE SET NULL,
    severity VARCHAR(10) DEFAULT 'medium',
    category VARCHAR(50),
    message TEXT NOT NULL,
    is_read VARCHAR(1) DEFAULT 'N' CHECK (is_read IN ('Y', 'N')),
    is_acknowledged VARCHAR(1) DEFAULT 'N' CHECK (is_acknowledged IN ('Y', 'N')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    details TEXT,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    file_path VARCHAR(255),
    file_size INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    title VARCHAR(100),
    description TEXT,
    generated_by INTEGER REFERENCES users(id),
    generated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Additional indexes
CREATE INDEX IF NOT EXISTS idx_medications_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_patient ON medication_intakes(patient_id);
CREATE INDEX IF NOT EXISTS idx_activity_events_patient ON activity_events(patient_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_patient ON recommendations(patient_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_reports_patient ON reports(patient_id);

-- ===========================================
-- Verification
-- ===========================================
SELECT 'Migration completed successfully!' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
