-- Migration: add new PenaltyReason enum values (good_behavior, no_violation_week)
-- (models.py now declares these, but Base.metadata.create_all() does NOT alter an
--  existing Postgres ENUM type on tables/types that already exist on Supabase.)
--
-- HOW TO RUN:
--   1. First check the real enum type name on your Supabase instance:
--        SELECT t.typname
--        FROM pg_type t
--        JOIN pg_enum e ON t.oid = e.enumtypid
--        GROUP BY t.typname;
--      Look for the type backing "penalty_strike.reason" (SQLAlchemy's default
--      naming for an unnamed Enum() column is the lowercased Python class name,
--      i.e. "penaltyreason" — swap it below if yours differs).
--   2. Run this file: psql "$DATABASE_URL" -f backend/migrations/002_penalty_reason_add_values.sql
--
-- Note: ALTER TYPE ... ADD VALUE cannot run inside the same transaction that
-- later USES the new value, but each statement below is safe on its own.
-- Safe to re-run: IF NOT EXISTS guards both.

ALTER TYPE penaltyreason ADD VALUE IF NOT EXISTS 'good_behavior';
ALTER TYPE penaltyreason ADD VALUE IF NOT EXISTS 'no_violation_week';
