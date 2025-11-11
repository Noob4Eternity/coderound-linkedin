-- LinkedIn Job Change Monitor - Supabase Schema
-- Run this SQL in your Supabase SQL Editor to create the tables

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Monitored profiles table - stores URLs to monitor for job changes
CREATE TABLE IF NOT EXISTS monitored_profiles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    name TEXT,  -- Optional: friendly name for the profile
    active BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    last_checked TIMESTAMPTZ,
    check_frequency_hours INTEGER DEFAULT 24
);

-- Create index on URL for faster lookups
CREATE INDEX IF NOT EXISTS idx_monitored_profiles_url ON monitored_profiles(url);
CREATE INDEX IF NOT EXISTS idx_monitored_profiles_active ON monitored_profiles(active);

-- Profiles table - stores current state of monitored profiles
CREATE TABLE IF NOT EXISTS profiles (
    id BIGSERIAL PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    name TEXT,
    headline TEXT,
    current_position TEXT,
    current_company TEXT,
    last_updated TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on URL for faster lookups
CREATE INDEX IF NOT EXISTS idx_profiles_url ON profiles(url);

-- Job history table - tracks all positions detected over time
CREATE TABLE IF NOT EXISTS job_history (
    id BIGSERIAL PRIMARY KEY,
    profile_url TEXT NOT NULL,
    position TEXT,
    company TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (profile_url) REFERENCES profiles(url) ON DELETE CASCADE
);

-- Create index for faster profile lookups
CREATE INDEX IF NOT EXISTS idx_job_history_profile_url ON job_history(profile_url);

-- Scrape history table - audit log of all scraping attempts
CREATE TABLE IF NOT EXISTS scrape_history (
    id BIGSERIAL PRIMARY KEY,
    profile_url TEXT NOT NULL,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    success BOOLEAN,
    error_message TEXT,
    raw_data JSONB
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_scrape_history_profile_url ON scrape_history(profile_url);
CREATE INDEX IF NOT EXISTS idx_scrape_history_scraped_at ON scrape_history(scraped_at DESC);

-- Job changes table - detected job changes with notification status
CREATE TABLE IF NOT EXISTS job_changes (
    id BIGSERIAL PRIMARY KEY,
    profile_url TEXT NOT NULL,
    name TEXT,
    old_position TEXT,
    old_company TEXT,
    new_position TEXT,
    new_company TEXT,
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    notified BOOLEAN DEFAULT FALSE
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_job_changes_profile_url ON job_changes(profile_url);
CREATE INDEX IF NOT EXISTS idx_job_changes_notified ON job_changes(notified);
CREATE INDEX IF NOT EXISTS idx_job_changes_detected_at ON job_changes(detected_at DESC);

-- Optional: Enable Row Level Security (RLS)
-- Uncomment these if you want to enable RLS

-- ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scrape_history ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE job_changes ENABLE ROW LEVEL SECURITY;

-- Create policies (example - adjust based on your security needs)
-- This allows authenticated users to read and write all data

-- CREATE POLICY "Allow all operations for authenticated users" ON profiles
--     FOR ALL USING (auth.role() = 'authenticated');

-- CREATE POLICY "Allow all operations for authenticated users" ON job_history
--     FOR ALL USING (auth.role() = 'authenticated');

-- CREATE POLICY "Allow all operations for authenticated users" ON scrape_history
--     FOR ALL USING (auth.role() = 'authenticated');

-- CREATE POLICY "Allow all operations for authenticated users" ON job_changes
--     FOR ALL USING (auth.role() = 'authenticated');

-- Or for service role access (recommended for backend scripts):
-- CREATE POLICY "Allow service role full access" ON profiles
--     FOR ALL USING (auth.role() = 'service_role');

-- Verify tables were created
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
AND table_name IN ('monitored_profiles', 'profiles', 'job_history', 'scrape_history', 'job_changes')
ORDER BY table_name;
