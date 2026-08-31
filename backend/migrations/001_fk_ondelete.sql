-- Migration: apply ON DELETE CASCADE / SET NULL to existing FKs
-- (models.py now declares these ondelete rules, but Base.metadata.create_all()
--  only creates missing tables -- it does NOT alter FK constraints on tables
--  that already exist on Supabase. Run this once against the shared DB.)
--
-- HOW TO RUN:
--   1. First check the real constraint names on your Supabase instance:
--        SELECT conname, conrelid::regclass AS table_name
--        FROM pg_constraint
--        WHERE contype = 'f'
--          AND conrelid::regclass::text IN ('favorite', 'penalty_strike', 'points_log', 'lost_item');
--   2. If the names differ from the *_fkey guesses below (default Postgres
--      naming for FKs created via SQLAlchemy create_all), swap them in.
--   3. Run this file: psql "$DATABASE_URL" -f backend/migrations/001_fk_ondelete.sql
--
-- Safe to re-run: each DROP uses IF EXISTS.

BEGIN;

-- favorite.user_id -> unified_user.id : CASCADE
ALTER TABLE favorite DROP CONSTRAINT IF EXISTS favorite_user_id_fkey;
ALTER TABLE favorite
    ADD CONSTRAINT favorite_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES unified_user(id) ON DELETE CASCADE;

-- favorite.bicycle_id -> bicycle.id : SET NULL
ALTER TABLE favorite DROP CONSTRAINT IF EXISTS favorite_bicycle_id_fkey;
ALTER TABLE favorite
    ADD CONSTRAINT favorite_bicycle_id_fkey
    FOREIGN KEY (bicycle_id) REFERENCES bicycle(id) ON DELETE SET NULL;

-- penalty_strike.user_id -> unified_user.id : CASCADE
ALTER TABLE penalty_strike DROP CONSTRAINT IF EXISTS penalty_strike_user_id_fkey;
ALTER TABLE penalty_strike
    ADD CONSTRAINT penalty_strike_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES unified_user(id) ON DELETE CASCADE;

-- points_log.user_id -> unified_user.id : CASCADE
ALTER TABLE points_log DROP CONSTRAINT IF EXISTS points_log_user_id_fkey;
ALTER TABLE points_log
    ADD CONSTRAINT points_log_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES unified_user(id) ON DELETE CASCADE;

-- points_log.penalty_id -> penalty_strike.id : SET NULL
ALTER TABLE points_log DROP CONSTRAINT IF EXISTS points_log_penalty_id_fkey;
ALTER TABLE points_log
    ADD CONSTRAINT points_log_penalty_id_fkey
    FOREIGN KEY (penalty_id) REFERENCES penalty_strike(id) ON DELETE SET NULL;

-- lost_item.user_id -> unified_user.id : CASCADE
ALTER TABLE lost_item DROP CONSTRAINT IF EXISTS lost_item_user_id_fkey;
ALTER TABLE lost_item
    ADD CONSTRAINT lost_item_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES unified_user(id) ON DELETE CASCADE;

-- lost_item.bicycle_id -> bicycle.id : CASCADE (column is NOT NULL, so SET NULL is not valid here)
ALTER TABLE lost_item DROP CONSTRAINT IF EXISTS lost_item_bicycle_id_fkey;
ALTER TABLE lost_item
    ADD CONSTRAINT lost_item_bicycle_id_fkey
    FOREIGN KEY (bicycle_id) REFERENCES bicycle(id) ON DELETE CASCADE;

COMMIT;
