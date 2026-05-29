# Database Initialization Guide

## Files

- `schema.sql` — All table definitions with UUID primary keys
- `02_seed_game_status.sql` — Populates game_status lookup table
- `02_seed_player_position.sql` — Populates player_position lookup table  
- `procedures.sql` — Upsert procedures for inserting/updating data
- `procedures_retrieval.sql` — Read-only retrieval functions (`fn_*`)
- `procedures_analysis.sql` — Multi-table analysis functions (`fn_*`)

## Execution Order

```bash
# 1. Connect to PostgreSQL
psql -h localhost -U postgres

# 2. Create database
CREATE DATABASE nfl_fantasy;

# 3. Run schema
\c nfl_fantasy
\i C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/DB/schema.sql

# 4. Seed lookup tables
CALL usp_seed_game_status();
CALL usp_seed_player_position();

# 5. Load upsert procedures
psql -h localhost -U postgres -d nfl_fantasy -f procedures.sql

# 6. Load retrieval functions
psql -h localhost -U postgres -d nfl_fantasy -f procedures_retrieval.sql

# 7. Load analysis functions
psql -h localhost -U postgres -d nfl_fantasy -f procedures_analysis.sql

# 8. Verify setup
SELECT 'Game Status' AS table_name FROM game_status LIMIT 1;
SELECT 'Player Position' AS table_name FROM player_position LIMIT 1;
SELECT 'Teams' AS table_name FROM teams LIMIT 1;
SELECT * FROM fn_get_all_teams();  -- Test a retrieval function
```

## Using in Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="nfl_fantasy",
    user="postgres",
    password="your_password"
)

cur = conn.cursor()

# Load schema
with open('schema.sql', 'r') as f:
    cur.execute(f.read())

# Load seed data
cur.execute("CALL usp_seed_game_status()")
cur.execute("CALL usp_seed_player_position()")

conn.commit()
```

## Verification Queries

```sql
-- Check tables exist
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY tablename;

-- Check stored procedures
SELECT proname, prokind, proargnames 
FROM pg_proc p
LEFT JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname = 'public'
ORDER BY proname;

-- Check lookup tables are seeded
SELECT status_code, description FROM game_status;
SELECT position_code, description FROM player_position;
```

## Notes

1. All primary keys are UUID (GUID)
2. All foreign key columns match their referenced PKs in UUID type
3. Use `usp_*` procedures to insert/update data (upsert semantics)
4. Use `fn_*` functions to read data (retrieval and analysis)
5. Teams keyed by `abbr` (stable); game-specific ESPN IDs stored in `game_team_espn_ids[]` and `games.home/away_espn_id`
