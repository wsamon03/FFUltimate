# FantasyFootball Database — Analysis Stored Procedures Reference

## Overview

This document describes multi-table retrieval procedures that simplify common analysis patterns. These procedures join `players`, `teams`, `games`, and all stat tables to provide ready-made analysis views.

---

## Table of Contents

| Procedure                                | Purpose                                    |
|-------------------------------------------|---------------------------------|
| `sp_get_player_game_complete(id, id)`    | All stats for a player in a single game   |
| `sp_get_player_season_complete(id, year)`| All stats for a player for an entire season|
| `sp_get_player_season_week_by_week(id, year)`| All stats for a player week by week    |
| `sp_get_player_career_complete(id)`      | All stats for a player for their career   |
| `sp_get_player_career_by_team(id)`       | All stats for a player across teams       |
| `sp_get_game_both_teams(id)`             | Both teams with all stats for a game      |
| `sp_get_team_season_complete(id, year)`  | All team stats for a season               |
| `sp_get_team_season_week_by_week(id, year)`| All team stats week by week             |
| `sp_get_team_career_complete(id)`        | All team stats for career                 |
| `sp_get_team_vs_opponent(id, id)`        | Head-to-head team stats                   |
| `sp_get_team_season_all_games(id, year)` | All games for a team in a season          |
| `sp_get_game_passing_leaders(id, limit)` | Top passers in a game                     |
| `sp_get_game_rushing_leaders(id, limit)` | Top rushers in a game                     |
| `sp_get_game_receiving_leaders(id, limit)`| Top receivers in a game                   |
| `sp_get_player_fantasy_stats(id)`        | Fantasy-ready stats for a player          |

---

## Player-Focused Procedures

### `sp_get_player_game_complete(p_player_id, p_game_id)`

**Purpose:** Get every stat a player has for a single game.

**Returns:** Complete player record for one game, including their team info, game info, both teams' stats, and all stat categories (passing, rushing, receiving, defense, returns, kicking, punting).

```sql
CALL sp_get_player_game_complete('a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid, '12345678-90ab-cdef-1234-567890abcdef'::uuid);

-- Returns:
-- | player_id | player_espn_id | player_name | position_code | team_name | team_espn_id |
-- | game_id   | game_espn_id   | game_date   | home_team_id  | away_team_id | season_year | week | status_code |
-- | team_pts  | pass_comp | pass_att | pass_yds | pass_td | pass_int | pass_sacked |
-- | rush_att | rush_yds | rush_td | rec_receptions | rec_targets | rec_yds | rec_td |
-- | def_solo | def_ast | def_sacks | def_tfl | def_pd | def_qb_hits | def_td | def_int |
-- | ret_kick_no | ret_kick_yds | ret_kick_td |
-- | ret_punt_no | ret_punt_yds | ret_punt_td |
-- | k_fg_make | k_fg_att | k_xp_make | k_xp_att |
-- | p_no | p_yds | p_in20 | p_tb | p_fc | p_blk | p_long |
```

**Use case:** Detailed game report for a specific player.

---

### `sp_get_player_season_complete(p_player_id, p_season_year)`

**Purpose:** Get every stat a player has for an entire season, grouped by week.

**Returns:** All stats for a player across all their games in a season, with weekly totals and season totals aggregated.

**Parameters:**
- `p_player_id` (UUID): Player ID from the players table
- `p_season_year` (INT): Season year (default: 2025)

```sql
CALL sp_get_player_season_complete(42, 2025);
```

**Returns columns:**
- Player info: `id`, `espn_id`, `name`, `position_code`, `team_name`, `team_espn_id`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- Team info: `team_pts_total`
- All stat categories with season totals and weekly breakdown
- `games_played`: Count of games

**Use case:** Season review for a player.

---

### `sp_get_player_season_week_by_week(p_player_id, p_season_year)`

**Purpose:** Get every stat a player has for each individual week of a season.

**Returns:** Week-by-week breakdown with all stats for each game. Useful for tracking progression and identifying trends.

**Parameters:**
- `p_player_id` (UUID): Player ID from the players table
- `p_season_year` (INT): Season year (default: 2025)

**Returns columns:**
- Player info: `id`, `espn_id`, `name`, `position_code`, `team_name`, `team_espn_id`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All stats for each game, with `yards` showing the player's primary yardage source
- `scoring_category`: 'high_scoring', 'low_scoring', or 'medium_scoring'

**Use case:** Track a player's weekly performance week by week.

---

### `sp_get_player_career_complete(p_player_id)`

**Purpose:** Get every stat a player has produced in their entire career (all seasons).

**Returns:** Career totals aggregated across all seasons, plus season-by-season breakdown.

**Parameters:**
- `p_player_id` (UUID): Player ID from the players table

**Returns columns:**
- Player info: `id`, `espn_id`, `name`, `position_code`
- Team info: `team_name`, `team_espn_id`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All stat categories with career totals
- `games_played`: Total career games

**Use case:** Full career profile for a player.

---

### `sp_get_player_career_by_team(p_player_id)`

**Purpose:** Get a player's stats broken down by each team they've played for.

**Returns:** Career stats grouped by team, showing production at each stop.

**Parameters:**
- `p_player_id` (UUID): Player ID from the players table

**Returns columns:**
- Player info: `id`, `espn_id`, `name`, `position_code`
- Team info: `team_name`, `team_espn_id`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All stats grouped by team
- `stat_leader`: 'pass', 'rush', 'rec', or 'none' showing primary yardage source for that team stint

**Use case:** Draft analysis for players who've played multiple seasons.

---

## Team-Focused Procedures

### `sp_get_game_both_teams(p_game_id)`

**Purpose:** Get all stats for both teams in a single game.

**Returns:** Complete game summary with both teams' full stats.

**Parameters:**
- `p_game_id` (UUID): Game ID from the games table

```sql
CALL sp_get_game_both_teams(1);
```

**Returns columns:**
- Game info: `game_espn_id`, `game_date`, `status_code`, `season_year`, `week`
- Home team: `team_name`, `team_espn_id`, `home_pts`, `home_off_yds`, `home_def_sacks`, `home_int`, etc.
- Away team: `team_name`, `team_espn_id`, `away_pts`, `away_off_yds`, `away_def_sacks`, `away_int`, etc.
- Score: `winning_team`, `point_margin`

**Use case:** Full game report.

---

### `sp_get_team_season_complete(p_team_id, p_season_year)`

**Purpose:** Get all stats for a single team for an entire season.

**Returns:** All stats for a team across all their games in a season, with weekly totals.

**Parameters:**
- `p_team_id` (UUID): Team ID from the teams table
- `p_season_year` (INT): Season year (default: 2025)

**Returns columns:**
- Team info: `team_id`, `team_espn_id`, `abbr`, `team_name`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All stats with `games_played`, `season_pts_total`, `season_off_yds`, `season_def_sacks`, `season_td_total`

**Use case:** Team season review.

---

### `sp_get_team_season_week_by_week(p_team_id, p_season_year)`

**Purpose:** Get all stats for a single team week by week for a season.

**Returns:** Weekly breakdown with all stats for each game.

**Returns columns:**
- Team info: `team_id`, `team_espn_id`, `abbr`, `team_name`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All stats with `scoring_category` and `defense_category` indicators

**Use case:** Team performance analysis over a season.

---

### `sp_get_team_career_complete(p_team_id)`

**Purpose:** Get all stats for a team across their entire franchise history.

**Returns:** Career totals across all seasons.

**Parameters:**
- `p_team_id` (UUID): Team ID from the teams table

**Returns columns:**
- Team info: `team_id`, `team_espn_id`, `abbr`, `team_name`
- All stat categories with career totals
- `games_played`: Total franchise games
- `career_pts_total`, `career_off_yds`, `career_def_sacks`, `career_td_total`

**Use case:** Franchise historical analysis.

---

### `sp_get_team_vs_opponent(p_team_id, p_opponent_id)`

**Purpose:** Get head-to-head stats between two teams.

**Returns:** All games between two teams with both teams' stats for each matchup.

**Parameters:**
- `p_team_id` (UUID): Team ID from the teams table for your team
- `p_opponent_id` (UUID): Team ID from the teams table for opponent

**Returns columns:**
- Game info: `game_espn_id`, `game_date`, `status_code`
- Team: `team_name`, `team_espn_id`
- Opponent: `opponent_name`, `opponent_espn_id`
- Team stats: `pts_total`, `off_total_yds`, `def_sacks`, `total_turnovers`
- Result: `W`, `L`, or `T`
- Point margin: `point_margin`
- Opponent stats: `opponent_pts`, `opponent_off_yds`, `opponent_def_sacks`

**Use case:** Head-to-head matchup analysis.

---

### `sp_get_team_season_all_games(p_team_id, p_season_year)`

**Purpose:** Get all games for a single team in a season.

**Returns:** Complete game log with team stats for each game.

**Parameters:**
- `p_team_id` (UUID): Team ID from the teams table
- `p_season_year` (INT): Season year (default: 2025)

**Returns columns:**
- Team info: `team_id`, `team_espn_id`, `abbr`, `team_name`
- Game info: `season_year`, `week`, `game_date`, `status_code`
- All team stats for each game

**Use case:** Team game log.

---

## Leaderboard Procedures

### `sp_get_game_passing_leaders(p_game_id, p_limit)`

**Purpose:** Get top passers in a single game.

**Parameters:**
- `p_game_id` (UUID): Game ID from the games table
- `p_limit` (INT): Number of rows to return (default: 20)

**Returns columns:**
- Player info: `player_espn_id`, `name`, `position_code`, `team_name`, `game_espn_id`, `game_date`
- Passing: `pass_comp`, `pass_att`, `pass_yds`, `pass_td`, `pass_int`, `pass_sacked`
- Rates: `ypc` (yards per carry), `pct` (completion %), `btr` (ball-to-ball ratio)

**Use case:** Game passing leaders report.

---

### `sp_get_game_rushing_leaders(p_game_id, p_limit)`

**Purpose:** Get top rushers in a single game.

**Returns columns:**
- Player info: `player_espn_id`, `name`, `position_code`, `team_name`, `game_espn_id`, `game_date`
- Rushing: `rush_att`, `rush_yds`, `rush_td`
- Rate: `ypc` (yards per carry)

**Use case:** Game rushing leaders report.

---

### `sp_get_game_receiving_leaders(p_game_id, p_limit)`

**Purpose:** Get top receivers in a single game.

**Returns columns:**
- Player info: `player_espn_id`, `name`, `position_code`, `team_name`, `game_espn_id`, `game_date`
- Receiving: `rec_receptions`, `rec_targets`, `rec_yds`, `rec_td`
- Rates: `ypr` (yards per reception), `rtc` (reception rate)

**Use case:** Game receiving leaders report.

---

## Fantasy-Focused Procedures

### `sp_get_player_fantasy_stats(p_player_id)`

**Purpose:** Get fantasy-ready stats for a player.

**Returns:** Fantasy production including calculated fantasy points using standard scoring (0.5 PPR).

**Parameters:**
- `p_player_id` (UUID): Player ID from the players table

**Returns columns:**
- Player info: `player_espn_id`, `name`, `position_code`, `team_name`
- Game info: `season_year`, `week`, `game_date`
- Yardage: `total_yards`
- TDs: `pass_td`, `rush_td`, `rec_td`, `kick_extra_pts`, `ret_td`, `def_td`
- Defense: `def_int`, `def_sacks`, `def_qb_hits`, `def_tackles`
- Fantasy points: `fantasy_points` (standard scoring)
- Games played

**Scoring formula:**
```
FP = Yards/10 + TD*4/6 + XP + Int + 0.5*Rec + Sack*2.5 + ...
```

**Use case:** Fantasy draft analysis, weekly start decisions.

---

## Usage Patterns

### Python Example: Season Player Review

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="nfl_fantasy",
    user="postgres",
    password="your_password"
)

cur = conn.cursor()

# Get a player's season stats
cur.execute("CALL sp_get_player_season_complete(%s, %s)", ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 2025))
rows = cur.fetchall()
cols = [desc[0] for desc in cur.description]

print(f"{'Player':<20} {'Week':<6} {'Date':<12} {'Yards':<10} {'TDs':<5} {'Points':<10}")
print("-" * 70)

for row in rows:
    player_name = row[2]  # player_name
    week = row[6]  # week
    date = row[7]  # game_date
    pass_yds = row[11] or 0  # pass_yds
    rush_yds = row[13] or 0  # rush_yds
    rec_yds = row[15] or 0  # rec_yds
    total_yds = pass_yds + rush_yds + rec_yds
    td = row[12] or 0  # pass_td
    rush_td = row[14] or 0  # rush_td
    rec_td = row[16] or 0  # rec_td
    xp = row[31] or 0  # k_xp_make
    total_td = td + rush_td + rec_td + (row[32] or 0) + (row[22] or 0) + (row[23] or 0)
    
    fantasy_pts = ((total_yds / 10) + (total_td * 4) + (row[31] or 0) * 1)
    
    print(f"{player_name:<20} {week:<6} {date:<12} {total_yds:<10} {total_td:<5} {fantasy_pts:.1f}")

cur.close()
conn.close()
```

### SQL Client Example: Team Season Review

```sql
-- Get Chiefs' 2025 season (using team UUID)
CALL sp_get_team_season_complete('b1c2d3e4-f5a6-7890-bcde-f12345678901'::uuid, 2025);
```

### SQL Client Example: Head-to-Head Report

```sql
-- Chiefs vs 49ers (using team UUIDs)
CALL sp_get_team_vs_opponent('b1c2d3e4-f5a6-7890-bcde-f12345678901'::uuid, 'c2d3e4f5-a6b7-8901-cdef-123456789012'::uuid);
```

### SQL Client Example: Season Week-by-Week

```sql
-- Kansas City's season week by week (using team UUID)
CALL sp_get_team_season_week_by_week('b1c2d3e4-f5a6-7890-bcde-f12345678901'::uuid, 2025);
```

---

## Procedure Reference Table

| Procedure                               | Parameters                          | Returns                              |
|-----------------------------------------|--------------|--------------|
| `sp_get_player_game_complete()`          | p_player_id::UUID, p_game_id::UUID   | Single game full stats               |
| `sp_get_player_season_complete()`        | p_player_id::UUID, p_season_year     | Season totals by week                |
| `sp_get_player_season_week_by_week()`    | p_player_id::UUID, p_season_year     | Weekly breakdown                     |
| `sp_get_player_career_complete()`        | p_player_id::UUID                    | Career totals across all seasons     |
| `sp_get_player_career_by_team()`         | p_player_id::UUID                    | Stats grouped by team                |
| `sp_get_game_both_teams()`               | p_game_id::UUID                      | Both teams with full stats           |
| `sp_get_team_season_complete()`          | p_team_id::UUID, p_season_year       | Season stats by week                 |
| `sp_get_team_season_week_by_week()`      | p_team_id::UUID, p_season_year       | Weekly breakdown                     |
| `sp_get_team_career_complete()`          | p_team_id::UUID                      | Franchise totals                     |
| `sp_get_team_vs_opponent()`              | p_team_id::UUID, p_opponent_id::UUID  | Head-to-head matchups                |
| `sp_get_team_season_all_games()`         | p_team_id::UUID, p_season_year       | Team's game log                      |
| `sp_get_game_passing_leaders()`          | p_game_id::UUID, p_limit             | Top passers in game                  |
| `sp_get_game_rushing_leaders()`          | p_game_id::UUID, p_limit             | Top rushers in game                  |
| `sp_get_game_receiving_leaders()`        | p_game_id::UUID, p_limit             | Top receivers in game                |
| `sp_get_player_fantasy_stats()`          | p_player_id::UUID                    | Fantasy production                  |

---

## Notes

1. **UUID IDs** — All procedures accept UUID values from the database tables (e.g., `players.id`, `teams.id`, `games.id`) as PostgreSQL UUID types.

2. **Default parameters** — Many procedures have default values for parameters (e.g., `p_season_year = 2025`) to simplify common queries.

3. **NULL handling** — Procedures return NULL for stats not applicable to a player (e.g., QBs have NULL rec stats).

4. **Season data** — Procedures work with the current season year by default. Pass a different year to query past or future seasons.

5. **Career data** — Career procedures aggregate across all seasons the player has data for.

6. **Table joins** — All procedures internally join the necessary tables to provide complete analysis views without requiring multiple queries.
