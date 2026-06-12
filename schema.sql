-- Створення таблиці профілю користувача
CREATE TABLE IF NOT EXISTS profile (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT 'Користувач',
    age INTEGER NOT NULL DEFAULT 28,
    target_systolic INTEGER NOT NULL DEFAULT 120,
    target_diastolic INTEGER NOT NULL DEFAULT 80,
    target_pulse INTEGER NOT NULL DEFAULT 75,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Створення таблиці вимірювань
CREATE TABLE IF NOT EXISTS measurements (
    id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    systolic INTEGER NOT NULL,
    diastolic INTEGER NOT NULL,
    pulse INTEGER NOT NULL,
    mood VARCHAR(100) DEFAULT 'Спокійний',
    notes TEXT DEFAULT '',
    atmospheric_pressure INTEGER,
    medication_taken BOOLEAN DEFAULT FALSE,
    activity_level VARCHAR(50) DEFAULT 'Низька',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Створення індексу для швидкого пошуку за часом
CREATE INDEX IF NOT EXISTS idx_measurements_timestamp ON measurements(timestamp);

-- Створення тригера для оновлення updated_at в таблиці profile
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_profile_updated_at ON profile;
CREATE TRIGGER update_profile_updated_at BEFORE UPDATE ON profile
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Вставка дефолтного профілю, якщо його немає
INSERT INTO profile (name, age, target_systolic, target_diastolic, target_pulse)
SELECT 'Користувач', 28, 120, 80, 75
WHERE NOT EXISTS (SELECT 1 FROM profile);
