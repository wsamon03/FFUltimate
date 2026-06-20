-- ============================================================
-- FantasyFootball Database — Complete Setup Script
-- ============================================================
-- Run this entire file once to create and initialize the database
--
-- Prerequisites:
--   1. Install PostgreSQL (https://www.postgresql.org/download/windows/)
--   2. Start PostgreSQL service
--   3. Open pgAdmin or psql command line
--
-- Execution:
--   psql -h localhost -U postgres -f C:/path/to/this/file.sql
-- ============================================================

\echo ''
\echo '============================================================'
\echo 'FantasyFootball Database Setup'
\echo '============================================================'
\echo ''

-- ============================================================
-- STEP 1: Create database
-- ============================================================
\echo 'Step 1: Creating database..'
CREATE DATABASE fantasyfootball
  WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TEMPLATE = template0;

\echo '  ✓ Database "fantasyfootball" created'
\echo ''

-- ============================================================
-- STEP 2: Connect to database and create schema
-- ============================================================
\echo 'Step 2: Creating tables and indexes..'
\connect fantasyfootball

-- Create all tables with UUID primary keys
\i C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/schema.sql

\echo '  ✓ All tables and indexes created'
\echo ''

-- ============================================================
-- STEP 3: Seed lookup tables
-- ============================================================
\echo 'Step 3: Seeding lookup tables..'

-- Seed game_status
CREATE OR REPLACE FUNCTION seed_game_status()
RETURNS void AS $$
BEGIN
  INSERT INTO game_status (status_code, description) VALUES
    ('scheduled', 'Game has not started'),
    ('live',     'Game is in progress'),
    ('final',    'Game is complete')
  ON CONFLICT (status_code) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

SELECT seed_game_status();

-- Seed player_position
CREATE OR REPLACE FUNCTION seed_player_position()
RETURNS void AS $$
BEGIN
  INSERT INTO player_position (position_code, description) VALUES
    ('QB', 'Quarterback'),
    ('RB', 'Running Back'),
    ('WR', 'Wide Receiver'),
    ('TE', 'Tight End'),
    ('K',  'Kicker'),
    ('DL', 'Defensive Lineman'),
    ('LB', 'Linebacker'),
    ('CB', 'Cornerback'),
    ('S',  'Safety'),
    ('DP', 'Defensive Player'),
    ('P',  'Punter'),
    ('HS', 'Defensive Specialist'),
    ('',   'Non-position / Special'),
    ('C',  'Center'),
    ('DE', 'Defensive End'),
    ('DT', 'Defensive Tackle'),
    ('FB', 'Fullback'),
    ('G',  'Guard'),
    ('LS', 'Long Snapper'),
    ('OT', 'Offensive Tackle'),
    ('PK', 'Placekicker')
  ON CONFLICT (position_code) DO NOTHING;
END;
$$ LANGUAGE plpgsql;

SELECT seed_player_position();

\echo '  ✓ Lookup tables seeded'
\echo ''

-- ============================================================
-- STEP 4: Create all stored procedures
-- ============================================================
\echo 'Step 4: Creating stored procedures..'

-- Load upsert procedures from file (paste content from procedures.sql)
\i C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/procedures.sql

-- Load retrieval procedures from file (paste content from procedures_retrieval.sql)
\i C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/procedures_retrieval.sql

-- Load analysis procedures from file (paste content from procedures_analysis.sql)
\i C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/procedures_analysis.sql

\echo '  ✓ All stored procedures created'
\echo ''

-- ============================================================
-- STEP 5: Verify setup
-- ============================================================
\echo 'Step 5: Verifying setup..'

-- List all tables
\echo 'Tables:'
SELECT tablename, tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- List stored procedures
\echo ''
\echo 'Stored Procedures:'
SELECT proname, pronamespace::regnamespace AS schema
FROM pg_proc p
WHERE pronamespace::regnamespace = 'public'
ORDER BY proname;

-- Show seeded data
\echo ''
\echo 'Seed Data:'
SELECT status_code, description FROM game_status ORDER BY status_code;
SELECT position_code, description FROM player_position ORDER BY position_code;

-- Count records
\echo ''
\echo '  ✓ Verification complete'
\echo ''

\echo '============================================================'
\echo 'Setup Complete!'
\echo '============================================================'
\echo ''
\echo 'Next steps:'
\echo '  1. Call seed procedures to populate lookup tables:'
\echo '     CALL usp_seed_game_status();'
\echo '     CALL usp_seed_player_position();'
\echo ''
\echo '  2. Begin inserting data using upsert procedures:'
\echo '     CALL usp_upsert_team(''200100001'', ''KC'', ''Kansas City Chiefs'');'
\echo ''
\echo '  3. Query data using retrieval procedures:'
\echo '     CALL sp_get_all_teams();'
\echo ''
\echo '  4. Run analysis queries:'
\echo '     CALL sp_get_team_season_complete(1, 2025);'
\echo ''
