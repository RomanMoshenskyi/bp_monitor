-- Нові таблиці для функціоналу медичних звітів та призначень ліків
-- BP Monitor - Extended Schema
-- Порядок створення важливий через Foreign Key залежності!

-- ============================================
-- 1. Таблиця медичних звітів лікаря (немає залежностей)
-- ============================================
CREATE TABLE IF NOT EXISTS doctor_reports (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Ідентифікація звіту
    report_number VARCHAR(50) NOT NULL UNIQUE,
    report_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Скарги та анамнез
    chief_complaint TEXT,
    history_illness TEXT,
    history_life TEXT,
    
    -- Об'єктивний огляд
    objective_exam TEXT,
    general_condition VARCHAR(100),
    consciousness VARCHAR(50),
    body_temperature VARCHAR(10),
    skin_condition VARCHAR(200),
    
    -- Вітальні показники
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    blood_pressure_sys INTEGER,
    blood_pressure_dia INTEGER,
    
    -- Серцево-судинна система
    heart_sounds VARCHAR(200),
    pulse_rhythm VARCHAR(50),
    pulse_character VARCHAR(100),
    
    -- Діагноз
    preliminary_diagnosis TEXT,
    final_diagnosis TEXT,
    diagnosis_code_icd VARCHAR(20),
    
    -- Результати обстежень
    ecg_results TEXT,
    xray_results TEXT,
    lab_results TEXT,
    other_exams TEXT,
    
    -- Лікування та призначення
    treatment_plan TEXT,
    prescriptions TEXT,
    procedures TEXT,
    lifestyle_recommendations TEXT,
    diet_recommendations TEXT,
    activity_recommendations TEXT,
    
    -- Заключення
    doctor_conclusion TEXT,
    prognosis VARCHAR(200),
    
    -- Наступне відвідування
    next_visit_date DATE,
    next_visit_reason VARCHAR(300),
    
    -- Лікарняний
    sick_leave_required BOOLEAN DEFAULT FALSE,
    sick_leave_days INTEGER,
    sick_leave_from DATE,
    sick_leave_to DATE,
    
    -- Підпис лікаря
    doctor_signature_name VARCHAR(200),
    doctor_position VARCHAR(200),
    doctor_specialty VARCHAR(200),
    signature_date TIMESTAMP,
    is_signed BOOLEAN DEFAULT FALSE,
    
    -- Файл звіту
    file_path VARCHAR(500),
    file_size INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Індекси для doctor_reports
CREATE INDEX IF NOT EXISTS idx_doctor_reports_doctor_id ON doctor_reports(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_reports_patient_id ON doctor_reports(patient_id);
CREATE INDEX IF NOT EXISTS idx_doctor_reports_report_date ON doctor_reports(report_date);

-- ============================================
-- 2. Таблиця призначень ліків (рецептів) - немає залежностей від інших нових таблиць
-- ============================================
CREATE TABLE IF NOT EXISTS prescriptions (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Ідентифікація призначення
    prescription_number VARCHAR(50) NOT NULL UNIQUE,
    prescription_date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Інформація про ліки
    medication_name VARCHAR(200) NOT NULL,
    medication_form VARCHAR(100),
    dosage VARCHAR(100) NOT NULL,
    
    -- Розклад прийому
    frequency_per_day INTEGER NOT NULL DEFAULT 1,
    specific_times TIME[],
    
    -- Тривалість
    duration_days INTEGER,
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    end_date DATE,
    
    -- Інструкції по прийому
    take_with_food BOOLEAN,
    take_before_food BOOLEAN,
    take_after_food BOOLEAN,
    special_instructions TEXT,
    
    -- Нотатки лікаря
    prescribed_for TEXT,
    contraindications TEXT,
    side_effects_notes TEXT,
    interactions_warning TEXT,
    
    -- Статус
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    
    -- Сповіщення пацієнту
    patient_notified BOOLEAN DEFAULT FALSE,
    notification_seen_at TIMESTAMP,
    notification_accepted BOOLEAN,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    cancelled_reason TEXT
);

-- Індекси для prescriptions
CREATE INDEX IF NOT EXISTS idx_prescriptions_doctor_id ON prescriptions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_patient_id ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescriptions_status ON prescriptions(status);
CREATE INDEX IF NOT EXISTS idx_prescriptions_prescription_date ON prescriptions(prescription_date);

-- ============================================
-- 3. Таблиця medications (посилається на prescriptions)
-- ============================================
CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    dosage REAL NOT NULL,
    unit VARCHAR(20) NOT NULL,
    frequency VARCHAR(100),
    notes TEXT,
    prescription_id INTEGER REFERENCES prescriptions(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_medications_patient_id ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medications_prescription_id ON medications(prescription_id);

-- ============================================
-- 4. Таблиця прийому ліків (посилається на medications та prescriptions)
-- ============================================
CREATE TABLE IF NOT EXISTS medication_intakes (
    id SERIAL PRIMARY KEY,
    medication_id INTEGER REFERENCES medications(id) ON DELETE CASCADE,
    prescription_id INTEGER REFERENCES prescriptions(id) ON DELETE SET NULL,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    measurement_id VARCHAR(50) REFERENCES measurements(id) ON DELETE SET NULL,
    
    -- Час прийому
    scheduled_time TIMESTAMP NOT NULL,
    taken_at TIMESTAMP,
    
    -- Дозування
    dosage_taken REAL,
    dosage_unit VARCHAR(20),
    
    -- Статус прийому
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    
    -- Прихильність
    taken_on_time BOOLEAN,
    minutes_delay INTEGER,
    
    -- Контекст прийому
    taken_with_food BOOLEAN,
    notes TEXT,
    skip_reason VARCHAR(200),
    
    -- Нагадування
    reminder_sent BOOLEAN DEFAULT FALSE,
    reminder_sent_at TIMESTAMP,
    reminder_acknowledged BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Індекси для medication_intakes
CREATE INDEX IF NOT EXISTS idx_medication_intakes_patient_id ON medication_intakes(patient_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_prescription_id ON medication_intakes(prescription_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_medication_id ON medication_intakes(medication_id);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_scheduled_time ON medication_intakes(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_medication_intakes_status ON medication_intakes(status);

-- ============================================
-- Тригери для оновлення updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_doctor_reports_updated_at ON doctor_reports;
CREATE TRIGGER update_doctor_reports_updated_at 
    BEFORE UPDATE ON doctor_reports 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_prescriptions_updated_at ON prescriptions;
CREATE TRIGGER update_prescriptions_updated_at 
    BEFORE UPDATE ON prescriptions 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_medications_updated_at ON medications;
CREATE TRIGGER update_medications_updated_at 
    BEFORE UPDATE ON medications 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

DROP TRIGGER IF EXISTS update_medication_intakes_updated_at ON medication_intakes;
CREATE TRIGGER update_medication_intakes_updated_at 
    BEFORE UPDATE ON medication_intakes 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
