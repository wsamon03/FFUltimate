# Game Score Ingestion Pipeline

## Overview

Scores (`home_score`, `away_score`) are denormalized into the `games` dimension table rather than fetched exclusively from `team_game_stats` fact tables. This eliminates joins for the primary game-list view.

## Pipeline Chain

```
ESPN API → parsers.py → models.py → engine.py → db_writer.py → stored procedure
```

### Step-by-Step

1. **`ingest/espn/parsers.py`** — `parse_summary()` extracts `home_team.score` and `away_team.score` from the boxscore competitors, assigns them to `home_score` and `away_score` on the `NormalizedGame` object.

2. **`ingest/espn/models.py`** — `NormalizedGame` dataclass includes:
   ```python
   home_score: Optional[int] = None
   away_score: Optional[int] = None
   ```

3. **`ingest/engine.py`** — `process_game()` passes scores positionally to `db_writer.upsert_game()`:
   ```python
   game_id = await self.db_writer.upsert_game(
       espn_id=parsed_game.espn_id,
       status_code=parsed_game.status_code,
       game_date=parsed_game.game_date,
       home_espn_id=parsed_game.home_team.espn_id,
       away_espn_id=parsed_game.away_team.espn_id,
       week=parsed_game.week,
       season_year=parsed_game.season_year,
       home_score=parsed_game.home_score,
       away_score=parsed_game.away_score,
   )
   ```

4. **`ingest/db_writer.py`** — `PgDBWriter.upsert_game()` accepts both scores and maps them to parameters `$8` and `$9`:
   ```python
   async def upsert_game(
       self, espn_id, status_code, game_date,
       home_espn_id, away_espn_id, week, season_year,
       home_score: int = None, away_score: int = None
   ) -> uuid.UUID:
       async with self.pool.acquire() as conn:
           await conn.execute(
               "CALL usp_upsert_game($1, $2, $3, $4, $5, $6, $7, $8, $9)",
               espn_id, status_code, game_date,
               str(home_espn_id), str(away_espn_id), home_score, away_score, week, season_year
           )
   ```

5. **`DB/procedures.sql`** — `usp_upsert_game` stored procedure accepts the score parameters and writes them into `games.home_score` and `games.away_score`.

## Frontend Retrieval

The games list API (`/api/games`) reads `home_score` and `away_score` directly from the `games` table columns with no JOINs:

```sql
SELECT g.id, g.espn_id, g.game_date, g.status_code, g.home_score, g.away_score, ...
FROM games g
JOIN teams h ON ...
JOIN teams a ON ...
```

## UI — Game ID Column

- **Location**: `ingest/frontend/index.html` — table column added after Status
- **Header**: `<th class="px-6 py-4">Game ID</th>`
- **Display**: `<td x-text="game.id.substring(0, 8)"></td>`
- **Purpose**: Shows internal DB UUID (8 chars) for stats tab navigation via `loadGameStats(game.id)`
