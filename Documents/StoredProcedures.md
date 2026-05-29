# FantasyFootball Database — Stored Procedures Reference

## Overview

This document describes every stored procedure in the NFL Fantasy Football database. All dimension-table procedures use **upsert** semantics: if a row with the same unique key exists, it is updated; otherwise a new row is inserted.

### Prerequisites

Before using the main procedures, run the seed procedures to populate lookup tables.

```sql
CALL usp_seed_game_status();
CALL usp_seed_player_position();
```

---

## Seed Procedures

### `usp_seed_game_status()`

Inserts the three valid game statuses. Safe to run repeatedly.

```sql
CALL usp_seed_game_status();
```

| status_code | Description        |
|------|-----|
| scheduled   | Game has not started |
| live        | Game is in progress  |
| final       | Game is complete     |

### `usp_seed_player_position()`

Inserts all valid NFL player positions. Safe to run repeatedly.

```sql
CALL usp_seed_player_position();
```

| position_code | Description               |
|------|------------|
| QB            | Quarterback               |
| RB            | Running Back              |
| WR            | Wide Receiver             |
| TE            | Tight End                 |
| K             | Kicker                    |
| DL            | Defensive Lineman         |
| LB            | Linebacker                |
| CB            | Cornerback                |
| S             | Safety                    |
| DP            | Defensive Player          |
| P             | Punter                    |
| HS            | Defensive Specialist      |

---

## Dimension Table Procedures

### `usp_upsert_team(p_espn_id, p_abbr, p_full_name)`

Upserts a team. Unique key: **espn_id**.

```sql
CALL usp_upsert_team(
    '200100001',   -- p_espn_id: ESPN team ID (e.g., from ESPN API)
    'KC',           -- p_abbr: 2-letter abbreviation
    'Kansas City Chiefs'  -- p_full_name: Full team name
);
```

| Parameter     | Type     | Required | Description               |
|------|----|----|------------|
| p_espn_id     | VARCHAR  | Yes      | ESPN's unique team ID     |
| p_abbr        | VARCHAR  | Yes      | 2-letter team abbreviation|
| p_full_name   | VARCHAR  | Yes      | Full team name            |

---

### `usp_upsert_player(p_espn_id, p_name, p_position_code, p_team_id)`

Upserts a player. Unique key: **espn_id**. The `team_id` must be the internal PostgreSQL ID from the `teams` table (not the ESPN ID).

```sql
CALL usp_upsert_player(
    '3116406',     -- p_espn_id: ESPN athlete ID
    'Patrick Mahomes',  -- p_name
    'QB',          -- p_position_code: must match a value in player_position table
    1              -- p_team_id: PK of the teams table (from teams.id)
);
```

| Parameter       | Type    | Required | Description                      |
|------|----|----|------------|
| p_espn_id       | VARCHAR | Yes      | ESPN's unique player ID          |
| p_name          | VARCHAR | Yes      | Player full name                 |
| p_position_code | VARCHAR | Yes      | Position code (from lookup table)|
| p_team_id       | INT     | Yes      | Internal team PK from teams table|

---

### `usp_upsert_game(p_espn_id, p_status_code, p_game_date, p_home_team_id, p_away_team_id, p_week, p_season_year)`

Upserts a game. Unique key: **espn_id**. All team IDs must be internal PostgreSQL IDs from the `teams` table.

```sql
CALL usp_upsert_game(
    '401671769',    -- p_espn_id: ESPN event ID
    'final',        -- p_status_code: must match game_status table
    '2025-09-04 20:20:00',  -- p_game_date: timestamp
    1,              -- p_home_team_id: internal team PK (home)
    2,              -- p_away_team_id: internal team PK (away)
    1,              -- p_week: NFL week number (1-18, or 19-22 for playoffs)
    2025            -- p_season_year
);
```

| Parameter       | Type    | Required | Description                      |
|------|----|----|------------|
| p_espn_id       | VARCHAR | Yes      | ESPN event ID                    |
| p_status_code   | VARCHAR | Yes      | Game status (from lookup table)  |
| p_game_date     | TIMESTAMP| Yes     | Game date and time               |
| p_home_team_id  | INT     | Yes      | Internal PK of home team         |
| p_away_team_id  | INT     | Yes      | Internal PK of away team         |
| p_week          | INT     | No       | NFL week number                  |
| p_season_year   | INT     | No       | NFL season year                  |

---

## Fact Table Procedures

### `usp_upsert_team_game_stats(...)`

Upserts team-level boxscore stats. Unique key: **(game_id, team_id)**. Both IDs must be internal PostgreSQL IDs from their respective tables.

```sql
CALL usp_upsert_team_game_stats(
    1,                              -- p_game_id: internal games.id
    1,                              -- p_team_id: internal teams.id
    30,                             -- p_pts_total
    7, 7, 8, 8, 0,                -- p_pts_q1, p_pts_q2, p_pts_q3, p_pts_q4, p_pts_ot
    3, 1, 0, 0,                   -- p_td_pass, p_td_rush, p_td_ret, p_td_def
    24, 412, 65,                  -- p_off_first_downs, p_off_total_yds, p_off_plays
    12, 6,                         -- p_off_3rd_att, p_off_3rd_make
    4, 3,                          -- p_off_redzone_att, p_off_redzone_td
    2010,                           -- p_off_possession_secs (MM:SS converted to seconds)
    2, 1,                           -- p_def_sacks (supports decimals like 1.5), p_def_int
    1,                              -- p_total_turnovers
    6, 45,                          -- p_penalties_count, p_penalties_yds
    '{"downs_defeated": 3}'::jsonb  -- p_metadata: optional additional stats
);
```

| Parameter           | Type         | Required | Description                       |
|------|----|----|------------|
| p_game_id           | INT          | Yes      | Internal games.id                 |
| p_team_id           | INT          | Yes      | Internal teams.id                 |
| p_pts_total         | INT          | No       | Total points                      |
| p_pts_q1            | INT          | No       | Q1 points                         |
| p_pts_q2            | INT          | No       | Q2 points                         |
| p_pts_q3            | INT          | No       | Q3 points                         |
| p_pts_q4            | INT          | No       | Q4 points                         |
| p_pts_ot            | INT          | No       | OT points                         |
| p_td_pass           | INT          | No       | Passing TDs                       |
| p_td_rush           | INT          | No       | Rushing TDs                       |
| p_td_ret            | INT          | No       | Return TDs                        |
| p_td_def            | INT          | No       | Defensive TDs                     |
| p_off_first_downs   | INT          | No       | First downs                        |
| p_off_total_yds     | INT          | No       | Total offensive yards              |
| p_off_plays         | INT          | No       | Total offensive plays              |
| p_off_3rd_att       | INT          | No       | 3rd down attempts                  |
| p_off_3rd_make      | INT          | No       | 3rd down conversions               |
| p_off_redzone_att   | INT          | No       | Red zone attempts                  |
| p_off_redzone_td    | INT          | No       | Red zone TDs                       |
| p_off_possession_secs | INT        | No       | Possession time in seconds         |
| p_def_sacks         | NUMERIC(3,1) | No       | Defensive sacks (supports 0.5)    |
| p_def_int           | INT          | No       | Defensive interceptions            |
| p_total_turnovers   | INT          | No       | Total turnovers                    |
| p_penalties_count   | INT          | No       | Number of penalties                |
| p_penalties_yds     | INT          | No       | Total penalty yards                |
| p_metadata          | JSONB        | No       | Unmapped niche stats               |

---

### `usp_upsert_player_game_stats(...)`

Upserts a player's boxscore stats. Unique key: **(player_id, game_id)**. Both IDs must be internal PostgreSQL IDs.

```sql
CALL usp_upsert_player_game_stats(
    42,                             -- p_player_id: internal players.id
    1,                              -- p_game_id: internal games.id
    28, 40, 354, 3, 1, 3,          -- p_pass_comp, p_pass_att, p_pass_yds, p_pass_td, p_pass_int, p_pass_sacked
    15, 72, 1,                     -- p_rush_att, p_rush_yds, p_rush_td
    NULL, NULL, NULL, NULL,         -- rec stats (not applicable to QB)
    0, 0, NULL, 0, 0, 0, 0, 0,     -- def stats (not applicable to QB)
    NULL, NULL, NULL,               -- kick return stats
    NULL, NULL, NULL,               -- punt return stats
    NULL, NULL, NULL, NULL,         -- kicking stats
    NULL, NULL, NULL, NULL, NULL, NULL, NULL,  -- punting stats
    NULL                            -- p_metadata
);
```

| Parameter         | Type         | Required | Description                        |
|------|----|----|------------|
| p_player_id       | INT          | Yes      | Internal players.id                |
| p_game_id         | INT          | Yes      | Internal games.id                  |
| p_pass_comp       | INT          | No       | Pass completions                   |
| p_pass_att        | INT          | No       | Pass attempts                      |
| p_pass_yds        | INT          | No       | Passing yards                      |
| p_pass_td         | INT          | No       | Passing TDs                        |
| p_pass_int        | INT          | No       | Interceptions thrown               |
| p_pass_sacked     | INT          | No       | Times sacked                       |
| p_rush_att        | INT          | No       | Rush attempts                      |
| p_rush_yds        | INT          | No       | Rushing yards                      |
| p_rush_td         | INT          | No       | Rushing TDs                        |
| p_rec_receptions  | INT          | No       | Receptions                         |
| p_rec_targets     | INT          | No       | Targets                             |
| p_rec_yds         | INT          | No       | Receiving yards                    |
| p_rec_td          | INT          | No       | Receiving TDs                      |
| p_def_solo        | INT          | No       | Solo tackles                        |
| p_def_ast         | INT          | No       | Assisted tackles                    |
| p_def_sacks       | NUMERIC(3,1) | No       | Defensive sacks (supports 0.5)     |
| p_def_tfl         | INT          | No       | Tackles for loss                   |
| p_def_pd          | INT          | No       | Passes defended                    |
| p_def_qb_hits     | INT          | No       | QB hits                             |
| p_def_td          | INT          | No       | Defensive TDs                      |
| p_def_int         | INT          | No       | Defensive interceptions             |
| p_ret_kick_no     | INT          | No       | Kick return number                 |
| p_ret_kick_yds    | INT          | No       | Kick return yards                  |
| p_ret_kick_td     | INT          | No       | Kick return TDs                    |
| p_ret_punt_no     | INT          | No       | Punt return number                 |
| p_ret_punt_yds    | INT          | No       | Punt return yards                  |
| p_ret_punt_td     | INT          | No       | Punt return TDs                    |
| p_k_fg_make       | INT          | No       | Field goals made                   |
| p_k_fg_att        | INT          | No       | Field goal attempts                |
| p_k_xp_make       | INT          | No       | Extra points made                  |
| p_k_xp_att        | INT          | No       | Extra point attempts               |
| p_p_no            | INT          | No       | Punts                               |
| p_p_yds           | INT          | No       | Punting yards                      |
| p_p_in20          | INT          | No       | Punts inside 20                    |
| p_p_tb            | INT          | No       | Punts returned touchbacks          |
| p_p_fc            | INT          | No       | Punts fair catch                   |
| p_p_blk           | INT          | No       | Punts blocked                      |
| p_p_long          | INT          | No       | Longest punt                        |
| p_metadata        | JSONB        | No       | Unmapped niche stats               |

---

## Usage Patterns

### Insert-First, Query-Later

The primary workflow for data ingestion:

```sql
-- 1. Seed lookups (one-time per environment)
CALL usp_seed_game_status();
CALL usp_seed_player_position();

-- 2. Ingest teams (upsert — safe to call multiple times)
CALL usp_upsert_team('200100001', 'KC', 'Kansas City Chiefs');
CALL usp_upsert_team('200100002', 'SF', 'San Francisco 49ers');

-- 3. Look up the internal team IDs after insertion
SELECT id, espn_id, abbr FROM teams WHERE espn_id IN ('200100001', '200100002');
-- Result: id 1 for KC, id 2 for SF

-- 4. Ingest a player (uses internal team PK)
CALL usp_upsert_player('3116406', 'Patrick Mahomes', 'QB', 1);

-- 5. Ingest a game (uses internal team PKs)
CALL usp_upsert_game('401671769', 'final', '2025-09-04 20:20:00', 1, 2, 1, 2025);

-- 6. Ingest team stats (uses internal IDs)
CALL usp_upsert_team_game_stats(
    1, 1, 30, 7, 7, 8, 8, 0,
    3, 1, 0, 0, 24, 412, 65, 12, 6, 4, 3, 2010, 2, 1, 1, 6, 45, NULL
);

-- 7. Look up the internal player ID for stat ingestion
SELECT id FROM players WHERE espn_id = '3116406';
-- Result: id 42

-- 8. Ingest player stats
CALL usp_upsert_player_game_stats(42, 1, 28, 40, 354, 3, 1, 3,
    16, 80, 1, 0, 0, 0, 0, 0,
    NULL, NULL, NULL, 0, 0, 0, 0, 0, 0,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL);
```

### Updating Existing Data

All upsert procedures are idempotent. Calling them again with the same `espn_id` or `(game_id, team_id)` will update the existing row rather than create a duplicate:

```sql
-- Update team name
CALL usp_upsert_team('200100001', 'KC', 'Kansas City City Chiefs');

-- Update game status from 'live' to 'final'
CALL usp_upsert_game('401671769', 'final', '2025-09-04 20:20:00', 1, 2, 1, 2025);

-- Update player stats after a correction
CALL usp_upsert_player_game_stats(42, 1, 29, 41, 360, 3, 0, 3,
    16, 80, 1, 0, 0, 0, 0, 0,
    NULL, NULL, NULL, 0, 0, 0, 0, 0, 0,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL);
```

---

## Table of Contents for Procedures

| Procedure                        | Table             | Unique Key              |
|-------------------------|------|----|----|
| `usp_seed_game_status()`         | game_status       | —                       |
| `usp_seed_player_position()`     | player_position   | —                       |
| `usp_upsert_team()`              | teams             | espn_id                 |
| `usp_upsert_player()`            | players           | espn_id                 |
| `usp_upsert_game()`              | games             | espn_id                 |
| `usp_upsert_team_game_stats()`   | team_game_stats   | (game_id, team_id)      |
| `usp_upsert_player_game_stats()` | player_game_stats | (player_id, game_id)    |
