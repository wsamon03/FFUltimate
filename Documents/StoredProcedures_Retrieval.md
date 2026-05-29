# FantasyFootball Database — Retrieval Stored Procedures Reference

## Overview

This document describes all retrieval stored procedures for reading data from the NFL Fantasy Football database. Unlike the upsert procedures (in [`StoredProcedures.md`](StoredProcedures.md)), these are **read-only** and used for querying, analyzing, and displaying data.

---

## Table of Contents

| Procedure                          | Purpose                              |
|------------------------------------|--------------------------------------|
| `sp_get_all_teams()`               | Fetch all teams                      |
| `sp_get_teams_by_espn_id()`        | Fetch teams by ESPN ID list          |
| `sp_get_team_by_espn_id()`         | Fetch single team by ESPN ID         |
| `sp_get_all_players()`             | Fetch all players                    |
| `sp_get_active_players()`          | Fetch active players (with filters)  |
| `sp_get_players_by_team()`         | Fetch players for a team             |
| `sp_get_players_by_espn_id()`      | Fetch players by ESPN ID list        |
| `sp_get_all_games()`               | Fetch all games                      |
| `sp_get_games_by_date_range()`     | Fetch games in date range            |
| `sp_get_games_by_espn_id()`        | Fetch games by ESPN ID list          |
| `sp_get_game_by_espn_id()`         | Fetch single game by ESPN ID         |
| `sp_get_team_stats_for_game()`     | Fetch team stats for a game          |
| `sp_get_team_stats_for_team()`     | Fetch all team stats for a team      |
| `sp_get_all_team_stats()`          | Fetch all team stats                 |
| `sp_get_team_stats_vs_opponent()`  | Fetch team stats vs specific opponent|
| `sp_get_player_stats_for_game()`   | Fetch player stats for a game        |
| `sp_get_player_stats_for_player()` | Fetch all stats for a player         |
| `sp_get_all_player_stats()`        | Fetch all player stats               |
| `sp_get_player_stats_vs_opponent()`| Fetch player stats vs specific opponent|
| `sp_get_player_stats_for_team()`   | Fetch all stats for players on team  |
| `sp_get_top_passers()`             | Fetch top passers for a game         |
| `sp_get_top_rushers()`             | Fetch top rushers for a game         |
| `sp_get_top_receivers()`           | Fetch top receivers for a game       |
| `sp_get_team_scoring_leaders()`    | Fetch top TD scorers for a game      |
| `sp_get_game_summary()`            | Fetch full game summary with both teams|
| `sp_get_top_scoring_teams()`       | Fetch top scoring teams (season/week)|

---

## Team Procedures

### `sp_get_all_teams()`

Returns all teams with their ESPN ID, abbreviation, and full name.

```sql
CALL sp_get_all_teams();

-- Returns:
-- | id | espn_id  | abbr | full_name             |
-- |----|----------|------|-----------------------|
-- | 1  | 200100001| KC   | Kansas City Chiefs    |
-- | 2  | 200100002| SF   | San Francisco 49ers   |
```

### `sp_get_teams_by_espn_id(p_espn_ids)`

Returns teams for a given list of ESPN IDs.

```sql
CALL sp_get_teams_by_espn_id(ARRAY['200100001', '200100002']);
```

### `sp_get_team_by_espn_id(p_espn_id)`

Returns a single team by ESPN ID.

```sql
CALL sp_get_team_by_espn_id('200100001');

-- Returns:
-- | id | espn_id  | abbr | full_name             |
-- |----|----------|------|-----------------------|
-- | 1  | 200100001| KC   | Kansas City Chiefs    |
```

### `sp_get_active_players(p_season_year, p_position_code)`

Returns players active for a season, optionally filtered by position.

```sql
CALL sp_get_active_players(2025, 'QB');

-- Returns:
-- | id | espn_id  | name            | position_code | team_id |
-- |----|----------|-----------------|----------------|---------|
-- | 42 | 3116406  | Patrick Mahomes | QB             | 1       |
```

### `sp_get_players_by_team(p_team_id)`

Returns all players on a specific team.

```sql
CALL sp_get_players_by_team(1);

-- Returns players for team with id=1 (Kansas City Chiefs)
```

---

## Game Procedures

### `sp_get_all_games()`

Returns all games with home/away team IDs, dates, and statuses.

```sql
CALL sp_get_all_games();

-- Returns:
-- | id | espn_id  | status_code | game_date           | home_team_id | away_team_id | week | season_year |
-- |----|----------|--------------|---------------------|---------------|--------------|------|-------------|
-- | 1  | 401671769| final        | 2025-09-04 20:20:00 | 1             | 2            | 1    | 2025        |
```

### `sp_get_games_by_date_range(p_start_date, p_end_date, p_season_year)`

Returns games within a date range for a season.

```sql
CALL sp_get_games_by_date_range('2025-09-04', '2025-09-10', 2025);
```

### `sp_get_games_by_espn_id(p_espn_ids)`

Returns games for a list of ESPN IDs.

### `sp_get_game_by_espn_id(p_espn_id)`

Returns a single game by ESPN ID with team details.

```sql
CALL sp_get_game_by_espn_id('401671769');

-- Returns:
-- | id | espn_id  | status_code | game_date           | home_team_id | away_team_id | week | season_year |
-- |----|----------|--------------|---------------------|---------------|--------------|------|-------------|
-- | 1  | 401671769| final        | 2025-09-04 20:20:00 | 1             | 2            | 1    | 2025        |
-- |    |          |              |                      | home_team_espn_id | home_team_name |
-- |    |          |              |                      | 1             | Kansas City Chiefs   |
```

---

## Team Stats Procedures

### `sp_get_team_stats_for_game(p_game_id)`

Returns all team stats for a specific game.

```sql
CALL sp_get_team_stats_for_game(1);

-- Returns:
-- | game_id | team_id | pts_total | pts_q1 | pts_q2 | pts_q3 | pts_q4 | pts_ot |
-- |---------|---------|-----------|--------|--------|--------|--------|--------|
-- | 1       | 1       | 30        | 7      | 8      | 8      | 7      | 0      |
-- | 1       | 2       | 24        | 7      | 7      | 8      | 2      | 0      |
```

### `sp_get_team_stats_for_team(p_team_id)`

Returns all team stats for a specific team across all games.

```sql
CALL sp_get_team_stats_for_team(1);

-- Returns: Kansas City Chiefs' season stats
```

### `sp_get_all_team_stats()`

Returns all team stats across all games.

```sql
CALL sp_get_all_team_stats();
```

### `sp_get_team_stats_vs_opponent(p_team_id, p_opponent_espn_id)`

Returns team stats when playing a specific opponent.

```sql
CALL sp_get_team_stats_vs_opponent(1, '200100002');

-- Returns: Kansas City stats when playing San Francisco
```

---

## Player Stats Procedures

### `sp_get_player_stats_for_game(p_game_id, p_player_id)`

Returns a single player's stats for a specific game.

```sql
CALL sp_get_player_stats_for_game(1, 42);

-- Returns: Patrick Mahomes' stats for game 1
```

### `sp_get_player_stats_for_player(p_player_id)`

Returns all stats for a single player across all games.

```sql
CALL sp_get_player_stats_for_player(42);

-- Returns: Patrick Mahomes' season stats
```

### `sp_get_all_player_stats()`

Returns all player stats across all games.

```sql
CALL sp_get_all_player_stats();
```

### `sp_get_player_stats_vs_opponent(p_player_id, p_opponent_espn_id)`

Returns a player's stats when playing a specific opponent.

```sql
CALL sp_get_player_stats_vs_opponent(42, '200100002');

-- Returns: Mahomes' stats vs San Francisco
```

### `sp_get_player_stats_for_team(p_team_id)`

Returns all stats for all players on a specific team.

```sql
CALL sp_get_player_stats_for_team(1);

-- Returns: All Chiefs players' season stats
```

---

## Analysis Procedures

### `sp_get_top_passers(p_game_id, p_limit)`

Returns the top passers by passing yards for a game.

```sql
CALL sp_get_top_passers(1, 5);

-- Returns: Top 5 passers by passing yards
-- Columns include pass_comp, pass_att, pass_yds, pass_td
```

### `sp_get_top_rushers(p_game_id, p_limit)`

Returns the top rushers by rushing yards for a game.

```sql
CALL sp_get_top_rushers(1, 5);

-- Returns: Top 5 rushers by rushing yards
```

### `sp_get_top_receivers(p_game_id, p_limit)`

Returns the top receivers by receiving yards for a game.

```sql
CALL sp_get_top_receivers(1, 5);

-- Returns: Top 5 receivers by receiving yards
```

### `sp_get_team_scoring_leaders(p_game_id)`

Returns the top TD scorers for a game (all positions).

```sql
CALL sp_get_team_scoring_leaders(1);

-- Returns: Top 5 TD scorers by total TDs (pass, rush, rec, ret)
-- Includes a fantasy_score column (TDs * 2 / team_pts * 100)
```

### `sp_get_game_summary(p_game_id)`

Returns a complete game summary with both teams' stats.

```sql
CALL sp_get_game_summary(1);

-- Returns:
-- | game_espn_id | game_date    | home_team_name | away_team_name | home_team_pts | away_team_pts | winning_team | point_diff |
-- |---------------|---------------|----------------|----------------|---------------|---------------|---------------|------------|
-- | 401671769    | 2025-09-04    | Kansas City    | San Francisco  | 30            | 24            | Kansas City  | 6          |
```

### `sp_get_top_scoring_teams(p_season_year, p_week, p_limit)`

Returns the top scoring teams for a season or week.

```sql
CALL sp_get_top_scoring_teams(2025, 1, 10);

-- Returns: Top 10 teams by total points in week 1
-- | team_id | team_espn_id | team_name | pts_total | off_total_yds | def_sacks | def_int |
```

---

## Usage Patterns

### Python (psycopg2)

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="nfl_fantasy",
    user="postgres",
    password="your_password",
    port=5432
)

cur = conn.cursor()

# Get all teams
cur.execute("CALL sp_get_all_teams()")
teams = cur.fetchall()
for team in teams:
    print(f"{team['id']}: {team['abbr']} ({team['full_name']})")

# Get top passers for a game
cur.execute("CALL sp_get_top_passers(%s, %s)", (1, 10))
top_passers = cur.fetchall()
for passer in top_passers:
    print(f"{passer['name']}: {passer['pass_yds']} yards, {passer['pass_td']} TDs")

conn.commit()
cur.close()
conn.close()
```

### SQL Client (psql, DBeaver, etc.)

```sql
-- Get all teams
CALL sp_get_all_teams();

-- Get all player stats
CALL sp_get_all_player_stats();

-- Get top 10 passers for game 1
CALL sp_get_top_passers(1, 10);
```

### Filtering Results

All procedures return columns as `rowtype` (PostgreSQL record). In Python/Pandas:

```python
import pandas as pd

cur.execute("CALL sp_get_top_passers(%s, %s)", (1, 10))
df = pd.DataFrame(cur.fetchall(), columns=cur.description)
print(df[['name', 'pass_yds', 'pass_td']])
```

### Using in Reports/Dashboards

```sql
-- Weekly recap query
CALL sp_get_games_by_date_range(
    '2025-09-01',
    '2025-09-07',
    2025
);

-- Combine with team stats to generate weekly report
```

---

## Procedure Reference Table

| Procedure                       | Parameters                              | Returns                          |
|---------------------------------|-----------------------------------------|----------------------------------|
| `sp_get_all_teams()`            | None                                    | All teams                        |
| `sp_get_teams_by_espn_id()`     | p_espn_ids: VARCHAR[]                   | Teams matching ESPN IDs          |
| `sp_get_team_by_espn_id()`      | p_espn_id: VARCHAR                      | Single team                      |
| `sp_get_all_players()`          | None                                    | All players                      |
| `sp_get_active_players()`       | p_season_year: INT, p_position_code: VARCHAR | Players for season/position |
| `sp_get_players_by_team()`      | p_team_id: INT                          | Players on team                  |
| `sp_get_players_by_espn_id()`   | p_espn_ids: VARCHAR[]                   | Players matching ESPN IDs        |
| `sp_get_all_games()`            | None                                    | All games                        |
| `sp_get_games_by_date_range()`  | p_start_date: DATE, p_end_date: DATE, p_season_year: INT | Games in range          |
| `sp_get_games_by_espn_id()`     | p_espn_ids: VARCHAR[]                   | Games matching ESPN IDs          |
| `sp_get_game_by_espn_id()`      | p_espn_id: VARCHAR                      | Single game                      |
| `sp_get_team_stats_for_game()`  | p_game_id: INT                          | Team stats for game              |
| `sp_get_team_stats_for_team()`  | p_team_id: INT                          | Team stats for team              |
| `sp_get_all_team_stats()`       | None                                    | All team stats                   |
| `sp_get_team_stats_vs_opponent()`| p_team_id: INT, p_opponent_espn_id: VARCHAR | Team stats vs opponent        |
| `sp_get_player_stats_for_game()`| p_game_id: INT, p_player_id: INT        | Player stats for game            |
| `sp_get_player_stats_for_player()`| p_player_id: INT                       | Player stats for player          |
| `sp_get_all_player_stats()`     | None                                    | All player stats                 |
| `sp_get_player_stats_vs_opponent()`| p_player_id: INT, p_opponent_espn_id: VARCHAR | Player stats vs opponent    |
| `sp_get_player_stats_for_team()`| p_team_id: INT                          | Player stats for team            |
| `sp_get_top_passers()`          | p_game_id: INT, p_limit: INT            | Top passers                      |
| `sp_get_top_rushers()`          | p_game_id: INT, p_limit: INT            | Top rushers                      |
| `sp_get_top_receivers()`        | p_game_id: INT, p_limit: INT            | Top receivers                    |
| `sp_get_team_scoring_leaders()` | p_game_id: INT                          | Top TD scorers                   |
| `sp_get_game_summary()`         | p_game_id: INT                          | Full game with both teams' stats |
| `sp_get_top_scoring_teams()`    | p_season_year: INT, p_week: INT, p_limit: INT | Top scoring teams             |

---

## Notes

1. **All procedures are deterministic** — they read data but never modify it.

2. **Parameter defaults** — Many procedures have default parameters (e.g., `p_limit DEFAULT 5`) to simplify common queries.

3. **ESPN ID vs internal ID** — Procedures that accept `espn_id` work with ESPN's unique identifiers; those that accept `id` work with PostgreSQL's internal auto-generated UUIDs.

4. **Date handling** — Date parameters accept `DATE` or `TIMESTAMP`. Pass a single date like `'2025-09-04'` for a full day's games.

5. **NULL handling** — NULL parameters use defaults (e.g., `p_season_year = 2025` by default).
