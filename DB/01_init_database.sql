-- NFL Fantasy Football Database — Initialization Script
-- Run this file to create the entire database from scratch
-- Execution order matters — do not reorder

\echo ''
\echo '=================================================='
\echo 'NFL Fantasy Football Database Initialization'
\echo '=================================================='
\echo ''
\echo 'Step 1: Creating database schema...'

-- Execute schema.sql to create all tables and indexes
\i DB/schema.sql

\echo ''
\echo '=================================================='
\echo 'Step 2: Loading lookup table seed data...'

-- Seed game_status lookup table
\i DB/02_seed_game_status.sql

-- Seed player_position lookup table
\i DB/02_seed_player_position.sql

\echo ''
\echo '=================================================='
\echo 'Step 3: Loading upsert stored procedures...'

-- Execute upsert procedures (dimension and fact tables)
\i DB/procedures.sql

\echo ''
\echo '=================================================='
\echo 'Step 4: Loading retrieval stored procedures...'

-- Execute retrieval procedures
\i DB/procedures_retrieval.sql

\echo ''
\echo '=================================================='
\echo 'Step 5: Loading analysis stored procedures...'

-- Execute analysis procedures
\i DB/procedures_analysis.sql

\echo ''
\echo '=================================================='
\echo 'Database initialization complete!'
\echo ''
\echo 'Next steps:'
\echo '  1. Run the seed files to populate lookup tables:'
\echo '     - DB/02_seed_game_status.sql'
\echo '     - DB/02_seed_player_position.sql'
\echo ''
\echo '  2. Begin inserting data via upsert procedures:'
\echo '     - Call usp_upsert_team(), usp_upsert_player(), etc.'
