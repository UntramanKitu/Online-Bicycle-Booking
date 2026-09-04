-- Migration: Create ENUM types for the BikeA system
-- This must be run BEFORE creating tables with SQLAlchemy metadata.create_all()

-- ==================== ENUM Types ====================
-- Core user & bicycle
CREATE TYPE IF NOT EXISTS user_role AS ENUM ('student', 'staff', 'officer');
CREATE TYPE IF NOT EXISTS user_status AS ENUM ('active', 'inactive', 'suspended');
CREATE TYPE IF NOT EXISTS bicycle_status AS ENUM ('available', 'in_use', 'under_maintenance', 'retired');
CREATE TYPE IF NOT EXISTS maintenance_type AS ENUM ('repair', 'routine_check', 'part_replacement');
CREATE TYPE IF NOT EXISTS maintenance_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');

-- Announcement
CREATE TYPE IF NOT EXISTS announcement_priority AS ENUM ('low', 'normal', 'high', 'urgent');
CREATE TYPE IF NOT EXISTS announcement_status AS ENUM ('draft', 'published', 'archived');

-- Booking (นายชัยอนันต์)
CREATE TYPE IF NOT EXISTS booking_type AS ENUM ('advance_reservation', 'walk_in');
CREATE TYPE IF NOT EXISTS booking_status AS ENUM ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show');

-- Group Ride (ตารางกลุ่มปั่นร่วมกัน — นายชัยอนันต์)
CREATE TYPE IF NOT EXISTS group_ride_status AS ENUM ('open', 'full', 'cancelled', 'completed');
CREATE TYPE IF NOT EXISTS group_ride_member_role AS ENUM ('leader', 'member');

-- Return & Damage
CREATE TYPE IF NOT EXISTS return_status AS ENUM ('normal', 'late', 'damaged', 'lost');
CREATE TYPE IF NOT EXISTS damage_severity AS ENUM ('minor', 'moderate', 'severe');

-- Favorite
CREATE TYPE IF NOT EXISTS favorite_target_type AS ENUM ('bicycle', 'station');

-- Notification
CREATE TYPE IF NOT EXISTS notification_type AS ENUM ('booking', 'return', 'penalty', 'system', 'promotion');
CREATE TYPE IF NOT EXISTS notification_channel AS ENUM ('in_app', 'email', 'sms');
CREATE TYPE IF NOT EXISTS notification_status AS ENUM ('pending', 'sent', 'read', 'failed');

-- Feedback
CREATE TYPE IF NOT EXISTS feedback_status AS ENUM ('visible', 'hidden', 'flagged');

-- Support Ticket (นายชัยอนันต์)
CREATE TYPE IF NOT EXISTS ticket_category AS ENUM ('bicycle_issue', 'account_issue', 'booking_issue', 'other');
CREATE TYPE IF NOT EXISTS ticket_priority AS ENUM ('low', 'normal', 'high', 'urgent');
CREATE TYPE IF NOT EXISTS ticket_status AS ENUM ('open', 'in_progress', 'resolved', 'closed', 'reopened');