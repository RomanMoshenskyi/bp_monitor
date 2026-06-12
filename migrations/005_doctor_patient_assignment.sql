-- Migration 005: doctor_patient_assignments table
-- Explicit many-to-many between doctors and patients.

CREATE TABLE IF NOT EXISTS doctor_patient_assignments (
    id          SERIAL PRIMARY KEY,
    doctor_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (doctor_id, patient_id)
);

CREATE INDEX IF NOT EXISTS idx_dpa_doctor  ON doctor_patient_assignments (doctor_id);
CREATE INDEX IF NOT EXISTS idx_dpa_patient ON doctor_patient_assignments (patient_id);
