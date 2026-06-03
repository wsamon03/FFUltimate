# Pi Memory - Global (Permanent) Knowledge
# Version 1.0 - 2026-06-03

---

## 🧪 Lesson #1: Environment Variable Cross-Session Persistence

**Problem**: `MOCK_ESPN=true` was set in the previous environment and persisted to this session's Python subprocesses.

**Root Cause**: Python subprocesses inherit environment variables from the **parent shell**, not from the main agent session. `os.environ` in Python is **read-only** once Python starts.

**Lesson**:
- Environment variables from sandboxed Python sessions **persist across agent runs**
- Cannot delete `MOCK_ESPN` from within Python after the process starts
- System-level environment variables persist across Python invocations

**Prevention**:
- Use dedicated `.env` files for test/dev environments
- Set `MOCK_ESPN=false` in startup scripts **immediately** (before Python spawns)
- Document in CI/CD pipelines: `export MOCK_ESPN=false` must run first

**Code Pattern**:
```python
# ✅ GOOD: Check env file on import
import os
if os.getenv('MOCK_ESPN') or 'MOCK_ESPN' in os.environ:
    # Use mock client
    pass

# ❌ BAD: Try to delete env var in Python
os.environ['MOCK_ESPN'] = 'false'  # Has no effect - inherited value
```

---

## 🧪 Lesson #2: PostgreSQL `ON CONFLICT ... DO UPDATE NULL Overwrite` Bug

**Problem**: `usp_upsert_player_game_stats` was using `column = EXCLUDED.column`, causing NULL stats from one category (e.g., rushing) to overwrite existing non-NULL values from another (e.g., passing).

**Example**:
```sql
-- Upsert 1: pass_yds=334, rush_yds=NULL
INSERT INTO player_game_stats (pass_yds=334, rush_yds=NULL)
ON CONFLICT (player_id, game_id) 
DO UPDATE SET pass_yds = EXCLUDED.pass_yds, rush_yds = EXCLUDED.rush_yds
-- After: pass_yds=334, rush_yds=NULL

-- Upsert 2: pass_yds=NULL, rush_yds=10
-- Triggered UPDATE:
DO UPDATE SET pass_yds = EXCLUDED.pass_yds  -- NULL overwrites 334!
                          rush_yds = EXCLUDED.rush_yds  -- INSERTS 10
-- Result: pass_yds=NULL, rush_yds=10 ❌
```

**Fix**:
- Changed all 38 stat columns from `column = EXCLUDED.column` to `column = COALESCE(EXCLUDED.column, pg.column)`
- **NULL values no longer overwrite existing data**, preserving player stats integrity

**Example**:
```sql
-- FIXED: COALESCE preserves non-NULL existing values
DO UPDATE SET rush_yds = COALESCE(EXCLUDED.rush_yds, player_game_stats.rush_yds)
              pass_yds = COALESCE(EXCLUDED.pass_yds, player_game_stats.pass_yds)  -- Keeps 334
```

**Critical for**: Multi-category players (WR+RUSH, QB+REC+RUSH)

---

## 🧪 Lesson #3: Mock vs Real Client Mixing

**Problem**: Using `MockESPNClient` for integration testing resulted in:
- `fetch_game_summary()` returning `None` for non-mocked events
- Only 5 hardcoded games (all Week 4) in MockESPNClient
- Ingestion reported "completed" with 0 ingested rows

**Lesson**:
- Always test with **real data** to catch data structure bugs
- Mock clients are valuable for **unit tests**, not integration testing
- Real API events can return `None` or empty data for games not in mocked set

**Pattern**:
```python
@pytest.mark.unit
def test_parse_boxscore_mock():
    # Test parsing logic with 5 mock games

@pytest.mark.integration
def test_ingestion_real():
    # Verify data structure with actual ESPN calls
```

---

## 🧪 Lesson #4: PostgreSQL Procedure Execution via Python

**Problem**: Re-creating stored procedures from within Python requires careful handling (autocommit, proper connection).

**Pattern**:
```python
import psycopg2
conn = psycopg2.connect(...)
conn.autocommit = True  # REQUIRED for single statement execution
cur = conn.cursor()
cur.execute('CREATE OR REPLACE PROCEDURE ...')
```

**Use Case**: Schema migrations that can't be run via `psql` CLI easily (multi-line CREATE statements, large procedures)

---

## 🧪 Lesson #5: Long-Running Services & Graceful Shutdown

**Problem**: Restarting uvicorn requires killing the process, waiting for cleanup, and verifying ports are free.

**Solution**: Use `wmic PROCESS WHERE ... delete` or `taskkill` for clean kills.

**Best Practices**:
1. List PIDs before killing (`tasklist /FI "PID eq <PID>"`)
2. Use `wmic PROCESS WHERE ... delete` for clean kills
3. Include `timeout /t 2 /nobreak` for graceful shutdown
4. Verify ports are free before starting new service

**Script Pattern**:
```bat
REM List PIDs to check
tasklist /FI "PID eq <PID>" /FO table
REM Kill old process
wmic PROCESS WHERE "executename='uvicorn' and PID >= 100000" delete
timeout /t 2 /nobreak  -- Let uvicorn cleanup threads
REM Verify free
netstat -ano ^| findstr "PORT" ^| findstr "LISTEN"
```

---

## 🧪 Lesson #6: Git Commit Discipline

**Problem**: Committing too much at once makes troubleshooting harder.

**Solution**:
- Commit **fixes independently** when possible
- Create `.bat`/`sh` wrapper scripts for common operations
- Document **why** each commit is needed

**Pattern**:
```bash
# Separate commits
git add -A
git commit -m "Fix: MockESPNClient always active due to MOCK_ESPN=true env var"

git add -A
git commit -m "Fix: COALESCE stored procedure bug - NULL stats overwrite existing values"
```

---

## 🧪 Lesson #8: `conn.transaction()` Scope in Asyncpg

**Problem**: `transaction()` is a **context manager on Connection**, not Pool.

**Correct Pattern**:
```python
async def process_transaction(pool: asyncpg.Pool):
    conn = await pool.acquire()
    try:
        async with conn.transaction():  # Transaction on CONNECTION
            await conn.execute(f"INSERT INTO ...")
    finally:
        await pool.release(conn)  # Return connection to pool
```

**Wrong Pattern**:
```python
async def process_transaction(pool: asyncpg.Pool):
    async with pool.transaction():  # This fails!
        ...
```

---

## 🧪 Lesson #9: JSONB/JSON Data Types in PostgreSQL

**Problem**: JSON/JSONB values are **always strings** in SQL queries.

**Rule**: Casting is required for comparisons.

**Example**:
```sql
-- ❌ WRONG
SELECT * FROM mytable WHERE json_column = 'data'

-- ✅ CORRECT
SELECT * FROM mytable WHERE json_column::JSONB = 'data'
```

---

**Last Updated**: 2026-06-03  
**Files Referenced**: 
- `TRANSACTION_GUIDELINES.md`
- `COALESCE_GUIDELINES.md`
- `MOCK_TESTS_GUIDELINES.md`
- `POSTGRESQL_SCHEMA_GUIDELINES.md`
- `clean-service-restart.md`
- `restart_services.bat`
