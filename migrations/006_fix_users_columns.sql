-- Fix users table columns to match ORM model
-- Add missing columns that ORM expects

ALTER TABLE users 
    ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS verification_token VARCHAR(255),
    ADD COLUMN IF NOT EXISTS specialization VARCHAR(100),
    ADD COLUMN IF NOT EXISTS primary_doctor_id INTEGER,
    ADD COLUMN IF NOT EXISTS threshold_profile_id INTEGER,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
