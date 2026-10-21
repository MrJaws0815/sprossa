-- Migration 001: Create waitlist table
-- Sprossa Beta-Warteschlange für die Mealime-Traffic-Welle

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS waitlist (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL UNIQUE,
    name        VARCHAR(200),
    household_size INTEGER,
    confirmed_at    TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_waitlist_email ON waitlist (email);

COMMENT ON TABLE waitlist IS 'Beta-Warteschlange – persistente E-Mail-Sammlung für den Sprossa-Launch';
COMMENT ON COLUMN waitlist.confirmed_at IS 'Gesetzt, wenn der Nutzer die Anmeldung bestätigt hat (Double-Opt-in)';