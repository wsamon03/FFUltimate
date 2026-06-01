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
