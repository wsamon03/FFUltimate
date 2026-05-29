# FantasyFootball Database Setup

## Files Created

### DB/
- `schema.sql` — All table definitions with UUID primary keys
- `setup.sql` — Complete database creation script (run once)
- `01_init_database.sql` — psql initialization script
- `02_seed_game_status.sql` — Seeds game_status lookup table
- `02_seed_player_position.sql` — Seeds player_position lookup table
- `procedures.sql` — Upsert stored procedures
- `procedures_retrieval.sql` — Read-only retrieval procedures
- `procedures_analysis.sql` — Multi-table analysis procedures
- `README.md` — Usage documentation

### Root
- `setup.ps1` — PowerShell setup script for Windows
- `README_DATABASE.md` — This file

## Setup Instructions

### Option 1: Using psql Command Line (Recommended)

```bash
# 1. Install PostgreSQL from https://www.postgresql.org/download/windows/
# 2. Add PostgreSQL bin folder to PATH or note the full path
# 3. Start PostgreSQL service (Services.msc → Start PostgreSQL)

# 4. Run setup script
psql -h localhost -U postgres -f C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/setup.sql
```

### Option 2: Using pgAdmin

1. Install pgAdmin if needed
2. Connect to PostgreSQL server
3. Create database: `fantasyfootball`
4. In Query Tool, paste content from `DB/schema.sql`
5. Execute the query
6. Paste and execute `02_seed_game_status.sql`
7. Paste and execute `02_seed_player_position.sql`
8. Paste and execute `procedures.sql`
9. Paste and execute `procedures_retrieval.sql`
10. Paste and execute `procedures_analysis.sql`

### Option 3: Using PowerShell

```powershell
cd C:\Users\qabct\Documents\Programming\FantasyFootball\Version2
.\setup.ps1
```

## Quick Start After Setup

```sql
-- Connect to database
psql -h localhost -U postgres -d fantasyfootball

-- Seed data
CALL usp_seed_game_status();
CALL usp_seed_player_position();

-- Insert sample data
CALL usp_upsert_team('200100001', 'KC', 'Kansas City Chiefs');
CALL usp_upsert_team('200100002', 'SF', 'San Francisco 49ers');

-- Query data
CALL sp_get_all_teams();
CALL sp_get_active_players(2025, 'QB');
```

## Troubleshooting

### "psql: command not found"
Add PostgreSQL bin folder to system PATH, or use full path:
```
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -U postgres -f DB/setup.sql
```

### "database already exists"
```sql
-- Drop and recreate
DROP DATABASE fantasyfootball;
CREATE DATABASE fantasyfootball;
```

### "permission denied"
Run PowerShell as Administrator, or:
- Open pgAdmin and connect as superuser
- Create database there

### "undefined function seed_game_status()"
Run the seed SQL files first:
```sql
--\i DB/02_seed_game_status.sql
--\i DB/02_seed_player_position.sql
```

## Verification Queries

```sql
-- Check tables
SELECT tablename FROM pg_tables ORDER BY tablename;

-- Check procedures
SELECT proname FROM pg_proc WHERE pronamespace::regnamespace = 'public' ORDER BY proname;

-- Check lookup tables are seeded
SELECT * FROM game_status;
SELECT * FROM player_position;
```

## Database Schema

- All primary keys: UUID (GUID)
- All foreign keys: UUID matching referenced PK
- Lookup tables: `game_status`, `player_position`
- Dimension tables: `teams`, `players`, `games`
- Fact tables: `team_game_stats`, `player_game_stats`

For more details, see `DB/README.md`.
