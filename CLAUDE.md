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

### UI — Game ID Column

*   **Location**: `ingest/frontend/index.html` — table column added after Status (`<th>Game ID</th>`) with display row `x-text="game.id.substring(0, 8)"`
*   **Purpose**: Shows the internal database UUID truncated to 8 chars (not the ESPN `espn_id`). Enables frontend to pass DB UUID to `loadGameStats(game.id)` for stats tab navigation.
