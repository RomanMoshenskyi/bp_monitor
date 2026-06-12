-- Migration 004: add soft-delete support
-- Run once; safe to re-run thanks to IF NOT EXISTS / column existence checks.

ALTER TABLE measurements
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

-- Partial index: only non-deleted measurements per user (speeds up all reads)
CREATE INDEX IF NOT EXISTS idx_measurements_active
    ON measurements (user_id, timestamp)
    WHERE deleted_at IS NULL;

-- Partial index: only active users
CREATE INDEX IF NOT EXISTS idx_users_active
    ON users (username)
    WHERE deleted_at IS NULL;
