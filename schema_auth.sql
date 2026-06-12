-- Користувачі та ролі
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('patient', 'doctor', 'admin')),
    age INTEGER,
    target_systolic INTEGER DEFAULT 120,
    target_diastolic INTEGER DEFAULT 80,
    target_pulse INTEGER DEFAULT 75,
    is_active BOOLEAN DEFAULT TRUE,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Порогові значення (глобальні, налаштовує адміністратор)
CREATE TABLE IF NOT EXISTS system_thresholds (
    id SERIAL PRIMARY KEY,
    systolic_high INTEGER NOT NULL DEFAULT 140,
    diastolic_high INTEGER NOT NULL DEFAULT 90,
    systolic_low INTEGER NOT NULL DEFAULT 90,
    diastolic_low INTEGER NOT NULL DEFAULT 60,
    pulse_high INTEGER NOT NULL DEFAULT 100,
    pulse_low INTEGER NOT NULL DEFAULT 50,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id)
);

INSERT INTO system_thresholds (systolic_high, diastolic_high, systolic_low, diastolic_low, pulse_high, pulse_low)
SELECT 140, 90, 90, 60, 100, 50
WHERE NOT EXISTS (SELECT 1 FROM system_thresholds);

-- Рекомендації лікаря
CREATE TABLE IF NOT EXISTS doctor_recommendations (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_patient ON doctor_recommendations(patient_id);

-- Прив'язка вимірювань до пацієнта
ALTER TABLE measurements ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_measurements_user_id ON measurements(user_id);
