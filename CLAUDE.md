
### User API Ã¢â‚¬â€ Service Architecture

*   **Dual-Service Pattern**: The system uses two separate services:
    *   **user_api (port 8001)** Ã¢â‚¬â€ OAuth/JWT auth, roster/favorites
    *   **ingest/api (port 8002)** Ã¢â‚¬â€ ESPN data ETL, game stats retrieval
*   **Why separate**: User management requires request-heavy auth handling; different security boundaries.
*   **Service boundary**: Both services share the same PostgreSQL database but serve different purposes.

### Cross-Dependency Pattern (user_api Ã¢â€ â€™ public)

*   **Constraint**: Tables in user_api schema reference public.players/public.teams.
*   **Impact**: Tight coupling Ã¢â‚¬â€ if public.players/teams schema changes, user_api breaks.
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

### User API Ã¢â‚¬â€ Stored Procedure Pattern

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
        *   HTTP 200 + `status: "success"` Ã¢â€ â€™ Data existed and was deleted
        *   HTTP 200 + `status: "warning"` Ã¢â€ â€™ No data found for deletion
        *   HTTP 500 + `status: "error"` Ã¢â€ â€™ Operation failed
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

*   **Flow**: `ESPN API Ã¢â€ â€™ parsers.py (extract score) Ã¢â€ â€™ models.py (NormalizedGame.home_score/away_score) Ã¢â€ â€™ engine.py (pass score param) Ã¢â€ â€™ db_writer.py (upsert_game $8/$9) Ã¢â€ â€™ stored procedure

*
    *   `ingest/espn/parsers.py` Ã¢â‚¬â€ extracts `home_team.score` and `away_team.score` and assigns to `home_score`/`away_score` in `NormalizedGame`
    *   `ingest/espn/models.py` Ã¢â‚¬â€ `home_score: int | None` and `away_score: int | None` added to `NormalizedGame`
    *   `ingest/engine.py` Ã¢â‚¬â€ passes `home_score` and `away_score` as positional args `$8` and `$9` to `db_writer.upsert_game()`
    *   `ingest/db_writer.py` Ã¢â‚¬â€ `upsert_game()` accepts `home_score`/`away_score` and calls `usp_upsert_game` with `CALL usp_upsert_game($1..$9)`
    *   `DB/procedures.sql` Ã¢â‚¬â€ `usp_upsert_game` signature

*   **Important**: The frontend retrieves `home_score` and `away_score` directly from `games` table columns with no joins to fact tables. The column order in the `games` table schema is: `season_year, week, home_code, away_code, time_tbd, status_code, game_date, home_score, away_score, id, home_team_id, away_team_id, espn_id`.


### User API Ã¢â‚¬â€ Service Architecture

*   **Dual-Service Pattern**: The system uses two separate services:
    *   **user_api (port 8001)** Ã¢â‚¬â€ OAuth/JWT auth, league/team management, roster/favorites
    *   **ingest/api (port 8002)** Ã¢â‚¬â€ ESPN data ETL, game stats retrieval, ingestion pipeline
*   **Why separate**: User management requires request-heavy auth handling; data ingestion is batch-heavy. Also different security boundaries (OAuth tokens vs. internal API).
*   **Service boundary**: Both services share the same PostgreSQL database but serve different purposes.

### Cross-Dependency Pattern (user_api Ã¢â€ â€™ public)

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
*   **Order**: Standard imports (os, logging, asyncpg) Ã¢â€ â€™ FastAPI imports (FastAPI, Query) Ã¢â€ â€™ Lifespan decorators

## Project-Specific Data & Frontend Rules (2026-06-10 Session)

### A. Rely on `/DB/procedures_retrieval.sql` for API Return Types
**Lesson**: FastAPI endpoints are thin wrappers over PostgreSQL functions prefixed with `fn_get_...`. The `RETURNS TABLE` definition is the absolute source of truth for column names and data shapes. Changing DB columns without checking the procedure breaks the entire stats layer.

**Rule 1**: **Always inspect `/DB/procedures_retrieval.sql`** before modifying or debugging a stats endpoint (e.g., `/api/stats/*`). Never guess schema fields based on variable names alone!

### B. Strict Naming Conventions for Teams & Games
**Lesson**: A single character in template keys like `team.abbreviation` vs `team.abbr` causes silent data failures (rendering `undefined`) or visual bugs across multiple components. 

**Rule 2**: The codebase strictly uses `abbr`, `espn_id`, and `full_name` for teams, and `home_team_abbr` / `away_team_abbr` for games. Never use generic aliases like `nickname`, `code`, or `abbreviation`.

### C. Client-Side Filtering is Mandatory for Game Queries
**Lesson**: The backend `/api/stats/games` endpoint lacks a native database-level `?team=` filter parameter. Sending it in the query string results in 0-filtered game lists.

**Rule 3**: Always fetch games by season/week first, then apply client-side filtering in Vue: 
```js
allGames.filter(g => 
    g.home_team_abbr.toLowerCase().includes(filter) || 
    g.away_team_abbr.toLowerCase().includes(filter)
)
```

### D. Prevent `${undefined}` URL Injections in Vue Templates
**Lesson**: Inside Vue templates, `undefined` properties inside template literals evaluate to the literal string `"undefined"`. Example: `:to="\`/nfl/games?team=${team.code}\`"` generates links like `/nfl/games?team=undefined`, which silently breaks filtering and routing.

**Rule 4**: Always chain valid fallbacks when using object properties in dynamic Vue URLs or state strings (e.g., `team.abbr || team.id`). Verify the property exists before interpolating it!

**Last

## Project-Specific DB & API Conventions (2026-06-14 Session)

### A. Safe Function Signature Updates in PostgreSQL
**Lesson**: `CREATE OR REPLACE` fails in PostgreSQL if the new function's return type changes (e.g., adding new score columns to `fn_get_all_games()`). It throws `cannot change return type of existing function`.

*Correct Pattern*: Always drop functions explicitly before recreating them if their signatures are changing:
```sql
DROP FUNCTION IF EXISTS fn_get_games_by_season(p_season INT);
CREATE OR REPLACE FUNCTION fn_get_games_by_season(p_season INT)...
```
**Rule**: Never assume a bare `CREATE OR REPLACE` works for signature expansions in `DB/procedures_retrieval.sql`.

### B. DB-to-UI Data Contract Alignment
**Lesson**: A mismatch between a router's response shape and the UI template causes silent crashes or "Not Found" errors (e.g., `/game/{id}` returning `{ game_id: "...", teams: [...] }` vs `NflGameDetailPage.vue` expecting flat fields like `home_team_abbr`).

**Rule**: Ensure FastAPI routes return the *exact* flattened column names expected by frontend templates. Do not wrap results in extra keys unless explicitly handled by theUI.

### C. UUID Casting Safety in asyncpg
**Lesson**: Implicit casting or casting DB columns (e.g., `g.id::text = $1`) in `asyncpg` can lead to silent data mismatches or strict type errors with FastAPI path parameters. 

**Rule**: Always cast query parameters explicitly when they interact with strict DB types like UUIDs: `WHERE g.id = $1::uuid`.

### D. SQL Join Column Aliasing Guardrail
**Lesson**: When querying joins (e.g., getting team abbrs for a games list), always alias columns explicitly using the table prefix (e.g., `t_home.abbr AS home_team_abbr`). 

**Rule**: Never rely on implicit column names from joins unless they are guaranteed to be unique across the entire query scope.

## Project Schema & Storage Rules

### A. Favorites Use a Unified Kind-Based Table
**Lesson**: The favorites feature consolidates both players and teams into a single `user_api.favorites` table rather than separate tables or arrays. It relies on a `kind` column (`'player' | 'team'`) to distinguish types, along with `target_name` and `extra` for cached display fields.
**Project Rule**: When querying or writing favorites, always expect the flat unified structure. Frontend components must `.filter()` by `kind` before mapping to component-specific shapes (e.g., separating players from NFL teams). Never assume the API returns nested `{ players: [], teams: [] }`.

### B. DB Migrations Are Split into Schema and Procedures
**Lesson**: Database definitions are intentionally separated in `/DB/`: DDL goes in `03_user_api_schema.sql` (tables, constraints, indexes), while logic/procedures live in `04_user_api_procedures.sql`.
**Project Rule**: When extending the database, keep schema definitions strictly in `03_*.sql` and move stored procedures/functions to `04_*.sql`. Do not mix DDL and procedural logic in the same migration file.

## Backend & API Architecture Rules

### C. Resource Endpoints Map 1:1 to Router Files
**Lesson**: The backend follows a strict `<resource>_router.py` pattern (e.g., `players_router.py`, `auth_router.py`). Each router handles its own pool dependency injection (`Depends(get_pool)`) and exposes endpoints under `/api/...` namespaces.
**Project Rule**: Always create or extend endpoints within the existing `<resource>_router.py` file rather than adding them to a central API wrapper. New routes should follow the established pool inheritance pattern (`pool: asyncpg.Pool = Depends(get_pool)`).

### D. Procedure INSERT Logic Uses Conditional CASE for Exclusive Columns
**Lesson**: Constraints like CHECK ((player_id IS NOT NULL AND team_id IS NULL) OR ...) mean stored procedures cannot blindly insert into both nullable columns. They must explicitly route values using `CASE WHEN kind = '...' THEN value ELSE NULL END`.
**Project Rule**: When modifying `usp_add_favorite` or similar procedures, always validate that conditional columns respect the CHECK constraint using explicit CASE routing rather than assuming automatic NULLIF propagation works.

## Ingestion Pipeline Patterns

### E. Season Discovery Relies on Week-by-Week Iteration
**Lesson**: The ingestion engine (`ingest/engine.py`) deliberately avoids bulk season discovery because external filters (like `type=2`) drop weeks/games silently. Instead, it uses constants like `WEEKS_REGULAR` and calls `process_week()` sequentially.
**Project Rule**: Any new data fetch loop in the ingestion module must follow the week-by-week iteration pattern. Do not attempt single-batch historical discovery until you verify the external API's pagination/filter limits explicitly.

### F. Diagnostic Endpoint for Data Completeness Monitoring
**Lesson**: The `/api/stats/season-summary` endpoint was added specifically to monitor ingestion health by reporting per-week game counts vs player_stat row counts.
**Project Rule**: When building new data pipelines, always include a lightweight diagnostic/status endpoint that reports entity counts by time period or status. Use it to verify completeness before trusting downstream UI displays.

## Frontend Component Conventions

### G. Dynamic PositionGroup Mapping Overrides Static Tables
**Lesson**: Player stat tables cannot share a static column layout. The project defines a `positionGroup` computed property in `<PlayerDetailPage>` and `<PlayersPage>` that maps raw position codes (`DL`, `LB`, `CB`, `S`) into UI groups (`DEF`), routing all data to position-specific `<template v-if="positionGroup === '...'">` blocks.
**Project Rule**: When adding new stat types or player positions, update the `positionGroup` computed mapping first, then define the corresponding columns inside the position-specific template block in both `PlayersPage.vue` and `PlayerDetailPage.vue`.

### H. Stats API Keys Must Match Database Abbreviations Exactly
**Lesson**: Frontend stats components (`LeaderboardTable.vue`, `PlayerStatRow.vue`) hardcode Vue template keys that exactly mirror PostgreSQL column abbreviations (e.g., `pass_yds`, `rec_receptions`, `def_solo`). There is no transformation layer between the API response key and the DOM key.
**Project Rule**: When updating backend DB columns or adding new stats, immediately sync the corresponding Vue template key in all referencing components. Assume the API returns exactly what the DB column name dictatesâ€”no camelCase conversion or aliasing happens at runtime.

## Auth & State Management Conventions

### I. Auth Store Exports `bootPromise` for Router Guard Synchronization
**Lesson**: The auth store initializes a module-level `\_bootResolve` function and exposes its linked `bootPromise`. This promise resolves in the `finally` block of `boot()`, ensuring it always fires regardless of success or failure refreshing from cookies.
**Project Rule**: If you need to await async initialization across multiple stores, follow the `\_bootResolve` + `new Promise<void>` pattern. Never use untyped boolean flags to synchronize loading states between Pinia stores and Vue Router guards.

### J. Helmet & Asset Directory Is Dedicated `/helmets/` Public Folder
**Lesson**: All team helmet images for NFL pages are stored directly under `frontend/public/helmets/{abbr}.png` rather than managed as imported assets or a CDN array.
**Project Rule**: When adding new teams or modifying helmet paths, reference them via the public route `<img src="/helmets/TEAM_ABBR.png">`. Do not import them into Vue setup blocks to avoid bundling overhead or relative path resolution issues during deployment.

### K. Frontend Isolation: Only user_api, Never ingest API
**Lesson**: The frontend **must** communicate exclusively with user_api (port 8001). The ingest API (port 8002) is for internal data ETL only. A critical violation occurred when stats endpoints were duplicated in ingest API with no auth gating.

*Pattern*: 
- Vite dev proxy routes all `/api/*` calls to `http://localhost:8001` (user_api)
- All user-facing endpoints live in `user_api/routers/stats_router.py` with `@Depends(get_current_user)` auth gates
- Ingest API's `retrieval_router.py` was removed; it duplicated user_api endpoints without auth
- If frontend needs stats data, add it to user_api, not ingest/api

**Project Rule**: Any feature requesting NFL stats must be implemented as a user_api endpoint with auth gating. Never add unauthenticated stats endpoints to the ingest service. Frontend always gets data through user_api gateway.

**Last Updated**: 2026-06-23
