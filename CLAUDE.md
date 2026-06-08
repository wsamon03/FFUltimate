
### User API — Service Architecture

*   **Dual-Service Pattern**: The system uses two separate services:
    *   **user_api (port 8001)** — OAuth/JWT auth, roster/favorites
    *   **ingest/api (port 8002)** — ESPN data ETL, game stats retrieval
*   **Why separate**: User management requires request-heavy auth handling; different security boundaries.
*   **Service boundary**: Both services share the same PostgreSQL database but serve different purposes.

### Cross-Dependency Pattern (user_api → public)

*   **Constraint**: Tables in user_api schema reference public.players/public.teams.
*   **Impact**: Tight coupling — if public.players/teams schema changes, user_api breaks.
*   **Tables**: roster_players, weekly_lineups, favorites reference public.players/public.teams.
*   **Rationale**: Keeps fantasy roster data separate from ESPN data layers.

### UUID vs. ESPN ID Pattern

*   **Pattern**: Frontend uses internal DB UUIDs (truncated to 8 chars) for navigation.
*   **Why**: ESPN IDs are 9-digit strings scoped to ESPN API. UUIDs are globally unique, stable.
*   **Pattern**: game.id.substring(0, 8) passed to route navigation.

### Lineup Replace Semantics

*   **Behavior**: Weekly lineups use replace semantics (clear old, then insert new).
*   **SQL**: leagues_router.py
    async with conn.transaction():
        await conn.execute("DELETE FROM user_api.weekly_lineups WHERE ...", team_id, season, week)
        for slot in slots:
            await conn.execute("INSERT INTO user_api.weekly_lineups ...", team_id, slot.player_id, season, week, slot.slot_position)
*   **Why**: Matches fantasy manager mental model.

### User API — Stored Procedure Pattern

*   **usp_add_league_team_owner**: Uses ON CONFLICT to handle multi-owner teams.
*   **usp_create_league_team**: Auto-assigns creator as commissioner.
*   **fn_get_user_favorites**: Uses UNION ALL to combine player and team favorites.
# CLAUDE.md

## Project Constraints & ESPN API Specifics

### ESPN NFL `/scoreboard` Endpoint Structure
When querying the NFL shortcut API endpoint (`/apis/site/v2/sports/football/nfl/scoreboard`):
*   **Event Location**: For this specific endpoint, game events are located at the **root level** of the JSON object (`response['events']`). Do not assume they are only nested inside `leagues`.
*   **Pagination**: Always use `params={'dates': YYYY, 'week': N}` to target specific weeks. Avoid calculating dates manually.

### NFL Ingestion Logic
*   **Sanity Check**: A standard NFL week contains **approximately 16 games**.
*   **Rule**: If your ingestion logs show **25+ games** for a specific week, you failed to filter by `week.number` correctly or used an incorrect date range.

### Database Stored Procedure Constraints
*   `usp_upsert_player_game_stats`: Requires exactly **41** arguments ($1...$41). Your Python `CALL` statement must match this count.
*   `usp_upsert_team_game_stats`: Requires exactly **26** arguments ($1...$26).
*   **Verification**: To avoid "No procedure matches" errors, verify argument counts via `SELECT proargnames FROM pg_proc WHERE proname = 'name';`.

### Retrieval Router Syntax (`ingest/service/retrieval_router.py`)
*   **Date Casting**: The endpoints expect input for `date_start` and `date_end`. When passing these string parameters to `asyncpg`, you **must** cast them to `::date` in your SQL query (e.g., `WHERE game_date::date >= $1`). If you do not, `asyncpg` will crash with an `AttributeError` because strings do not have the `toordinal` method required for datetime comparison.

### DELETE API Operation Patterns
*   **Zero-Row Detection**: `DELETE` commands **always return HTTP 200** even when zero rows are affected. Always verify with `SELECT COUNT(*)` before `DELETE`.
    *   **Pattern**: `SELECT COUNT(*) FROM table WHERE condition` BEFORE `DELETE FROM table WHERE condition`
    *   **Response Contract**:
        *   HTTP 200 + `status: "success"` → Data existed and was deleted
        *   HTTP 200 + `status: "warning"` → No data found for deletion
        *   HTTP 500 + `status: "error"` → Operation failed
*   **Never Delete Unless Matched**: Always run `COUNT(*)` check before deletion to avoid deleting records that don't exist

### FastAPI Query Parameter Validation
*   **Validate Before Deletion**: Use `@app.delete("{/id}", ...)` with `Query(...)` parameters
*   **Parameter Validation**: Always validate parameters before deletion checks (catches malformed requests early)
*   **Range Validation**: Match validation ranges to actual data (don't assume weeks = 1-18, use 0-22 for ESPN)

### Ingest Pipeline Verification
*   **Verify Column Columns**: Always verify `ingest/engine.py` populates `week` and `season_year` columns before attempting `DELETE` operations
*   **Check Procedure Output**: `usp_upsert_game(..., week, season_year)` writes columns into DB
*   **Match Pipeline**: Delete operations must match exactly what `ingest/engine.py` writes (column values, column names)

### asyncpg 0.31 Connection & Transaction Patterns
*   **Transaction Scope**: `transaction()` context manager belongs to **Connection** object, NOT Pool
    *   **Correct**: `async with POOL.acquire() as conn: async with conn.transaction(): await conn.execute(...)`
    ```

### ESPN Week Validation
*   **Week Range**: ESPN returns weeks 1-18 (normal) but can return 0 or 19-22 for playoffs
*   **Validation Rule**: Validate `week` parameter as `0` to `22` (not assumed to be 1-18)
*   **Season Year Field**: ESPN uses `season_year` (league year) as integer, typically matches Super Bowl year

### Delete API Pattern Example

```python
@app.delete("/api/delete/week")
async def delete_week(year: int = Query(...), week: int = Query(...)):
    """Delete all data for a given year-week"""
    try:
        # 1. Validate
        if week < 0 or week > 22:
            return {"status": "error", "message": "Week must be 0-22"}
        
        # 2. Check what matches BEFORE deleting
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM games WHERE season_year = $1 AND week = $2",
            year, week
        )
        
        # 3. Return warning if no data found
        if count == 0:
            return {
                "status": "warning",
                "message": "No data found for deletion",
                "details": {"year": year, "week": week, "games_matching": 0}
            }
        
        # 4. Delete with transparency
        await conn.execute("DELETE FROM games WHERE season_year = $1 AND week = $2", year, week)
        await conn.execute("DELETE FROM player_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1 AND week = $2)", year, week)
        await conn.execute("DELETE FROM team_game_stats WHERE game_id IN (SELECT id FROM games WHERE season_year = $1 AND week = $2)", year, week)
        
        return {"status": "success", "message": f"Week deleted ({count} games removed)"}
    except Exception as e:
        logger.error(f"Failed to delete week {year}-{week}: {e}")
        return {"status": "error", "message": "Delete failed", "error": str(e)}
```

### Ingest Engine Column Mapping

| Input Column | Ingest Output | DB Column | Procedure Parameter |
|------|------|------|------|
| `season` | `season_year` | `games.season_year` | `p_season_year` |
| `week` | `week` | `games.week` | `p_week` |
| `status` | `status_code` | `games.status_code` | `p_status_code` |
| `game_date` | `NormalizedGame.game_date` | `games.game_date` | Passed through |

**Key Insight**: Match `DELETE` SQL to exactly what `ingest/engine.py` writes to `usp_upsert_game()` to avoid zero-match bugs.

### Game Score Schema Design

*   **Core Lesson**: Denormalize match results (`home_score`, `away_score`) into the `games` table rather than relying exclusively on fact tables (`team_game_stats`).
*   **Why**: Fetching the score requires JOINs to the fact tables. Keeping it in the dimension table makes the primary display/API significantly faster and prevents schema coupling issues.
*   **Rule**: The `games` table must serve as the authoritative source for game metadata and final scores. Always update `games` alongside stats.

### Game Scores Ingestion Pipeline Chain

*   **Flow**: `ESPN API → parsers.py (extract score) → models.py (NormalizedGame.home_score/away_score) → engine.py (pass score param) → db_writer.py (upsert_game $8/$9) → stored procedure

*   **Updated files**:
    *   `ingest/espn/parsers.py` — extracts `home_team.score` and `away_team.score` and assigns to `home_score`/`away_score` in `NormalizedGame`
    *   `ingest/espn/models.py` — `home_score: int | None` and `away_score: int | None` added to `NormalizedGame`
    *   `ingest/engine.py` — passes `home_score` and `away_score` as positional args `$8` and `$9` to `db_writer.upsert_game()`
    *   `ingest/db_writer.py` — `upsert_game()` accepts `home_score`/`away_score` and calls `usp_upsert_game` with `CALL usp_upsert_game($1..$9)`
    *   `DB/procedures.sql` — `usp_upsert_game` signature updated: `CALL usp_upsert_game($1, $2, $3, $4, $5, $6, $7, $8, $9)` where `$6` = home_score, `$7` = away_score

*   **Important**: The frontend retrieves `home_score` and `away_score` directly from `games` table columns with no joins to fact tables. The column order in the `games` table schema is: `season_year, week, home_code, away_code, time_tbd, status_code, game_date, home_score, away_score, id, home_team_id, away_team_id, espn_id`.


### User API — Service Architecture

*   **Dual-Service Pattern**: The system uses two separate services:
    *   **user_api (port 8001)** — OAuth/JWT auth, league/team management, roster/favorites
    *   **ingest/api (port 8002)** — ESPN data ETL, game stats retrieval, ingestion pipeline
*   **Why separate**: User management requires request-heavy auth handling; data ingestion is batch-heavy. Also different security boundaries (OAuth tokens vs. internal API).
*   **Service boundary**: Both services share the same PostgreSQL database but serve different purposes.

### Cross-Dependency Pattern (user_api → public)

*   **Constraint**: Tables in user_api schema reference public.players/public.teams.

### FastAPI Route & Import Patterns

*   **Query Parameter Conflict**: FastAPI cannot combine `{event_id}` (path param) with `Query(...)` for the same parameter name
    *   **Wrong**: `@app.delete("/api/delete/{event_id}", ...)` with `async def delete_game(event_id: str = Query(...)):`
    *   **Correct**: Use `@app.delete("/api/delete/{event_id}", response_model=dict)` and let FastAPI auto-detect path param (no Query needed)
    *   **Or**: Use `@app.delete("/api/delete", ...)` with `Query()` for query-only deletion

*   **Import Placement**: Imports must be at module level, not inside exception handlers or function bodies
    *   **Wrong**: `import re` inside `try: ... except: import re` block
    *   **Correct**: `import re` at top of file with other imports

*   **Route Import Order**: Standard imports first, then FastAPI imports, then lifespan decorator
    ```python
    # Standard imports first
    import os
    import logging
    from contextlib import asynccontextmanager
    from dotenv import load_dotenv
    import asyncpg
    
    # FastAPI imports (after standard)
    from fastapi import FastAPI, Depends, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from ingest.service.ingestion_router import router as ingestion_router
    from ingest.service.retrieval_router import router as retrieval_router
    
    # Lifespan decorator
    @app.on_event("startup")
    async def on_startup()
    ```

*   **Function Indentation**: FastAPI route decorators require clean indentation without extra lines between decorator and function

### Frontend (Alpine.js) Debugging

*   **Missing Variable Reference**: JavaScript variable must match exactly (case-sensitive, property name)
    *   **Symptom**: `Uncaught ReferenceError: variableName is not defined` in Alpine.js render functions
    *   **Example**: Function uses `params.event_id` but undefined `gameId` exists
    *   **Pattern**: Always reference from `params` object which contains the delete criteria
    *   **Fix**: Changed from `gameId` to `params.event_id` in `performDeletion()` when it references `confirmDeletion()` variables

### Full UUID Display Pattern

*   **Use Case**: Show complete UUIDs in tables for easy UX when copying for API operations
*   **Frontend**: Use `x-text="item.id"` instead of `x-text="item.id.substring(0, 8)"`
*   **Example**: 
    *   **Before**: Game ID column shows `37da815b` (truncated to 8 chars)
    *   **After**: Game ID column shows `37da815b-0da4-404d-b142-3c89ee329548` (full UUID)
*   **Benefit**: Users can copy the full UUID directly from the table to use in delete operations

### Backend Service Restart Protocol

*   **Working Directory**: Backend must be run from root directory (where `ingest/` is a package)
*   **Running From Wrong Directory**: `ModuleNotFoundError: No module named 'ingest'` when running from `ingest/service/` directory
*   **Proper Method**: Use `python -m uvicorn ingest.service.app:app --host 127.0.0.1 --port 8002 --reload` from repo root with `PYTHONPATH` set
*   **Port 8002**: Backend runs on `http://localhost:8002`, frontend on `http://localhost:8000`

### Database Import & Import Order

*   **Placement**: All imports must be at module level
*   **Exception Block Imports**: `import re` inside exception handlers is a bug that causes 422 validation errors
*   **Order**: Standard imports (os, logging, asyncpg) → FastAPI imports (FastAPI, Query) → Lifespan decorators
