-- Migration 002: Add Double-Opt-in fields to waitlist table
-- Erweitert die waitlist-Tabelle um Token + Timestamps für den Bestätigungs-Flow

ALTER TABLE waitlist ADD COLUMN IF NOT EXISTS confirmation_token VARCHAR(128);
ALTER TABLE waitlist ADD COLUMN IF NOT EXISTS confirmation_sent_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE waitlist ADD COLUMN IF NOT EXISTS confirmed_at       TIMESTAMP WITH TIME ZONE;
ALTER TABLE waitlist ADD COLUMN IF NOT EXISTS confirmed_ip       VARCHAR(45);

CREATE INDEX IF NOT EXISTS idx_waitlist_confirmation_token ON waitlist (confirmation_token) WHERE confirmation_token IS NOT NULL;

COMMENT ON COLUMN waitlist.confirmation_token IS 'Einmal-Token für Double-Opt-in (24h gültig)';
COMMENT ON COLUMN waitlist.confirmation_sent_at IS 'Zeitpunkt des E-Mail-Versands';
COMMENT ON COLUMN waitlist.confirmed_at IS 'Zeitpunkt der Bestätigung (DOI-Klick). NULL = unbestätigt';
COMMENT ON COLUMN waitlist.confirmed_ip IS 'IP-Adresse bei Bestätigung (DSGVO-Nachweis)';