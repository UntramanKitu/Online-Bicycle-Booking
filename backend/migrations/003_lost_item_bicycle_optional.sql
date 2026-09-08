-- Migration: lost_item.bicycle_id becomes optional (nullable, ON DELETE SET NULL)
-- (models.py now declares this, but create_all() does not alter existing columns
--  or FK rules on tables that already exist on Supabase.)
--
-- HOW TO RUN:
--   1. Check the real constraint name if it differs from the *_fkey guess below:
--        SELECT conname FROM pg_constraint
--        WHERE conrelid = 'lost_item'::regclass AND contype = 'f';
--   2. Run this file: psql "$DATABASE_URL" -f backend/migrations/003_lost_item_bicycle_optional.sql
--
-- Safe to re-run: each step uses IF EXISTS / DROP+re-add.

BEGIN;

ALTER TABLE lost_item ALTER COLUMN bicycle_id DROP NOT NULL;

ALTER TABLE lost_item DROP CONSTRAINT IF EXISTS lost_item_bicycle_id_fkey;
ALTER TABLE lost_item
    ADD CONSTRAINT lost_item_bicycle_id_fkey
    FOREIGN KEY (bicycle_id) REFERENCES bicycle(id) ON DELETE SET NULL;

COMMIT;
