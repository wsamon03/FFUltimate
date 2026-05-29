# NFL Data Ingestion API Documentation

## Overview

The NFL Data Ingestion API provides endpoints for ingesting NFL game data from sports APIs and retrieving stats from the PostgreSQL database. It uses a provider-agnostic architecture where ESPN is the default provider, but others can be added via the abstract interface contracts.

## Running the Service

```bash
# Start the API server
python -m ingest --service
```

The server runs on `http://0.0.0.0:8000` with auto-generated Swagger docs at `http://localhost:8000/docs`.

## Ingestion API

### Ingest a Single Game

```
POST /api/ingest/game
```

| Parameter | Required | Type   | Description             |
|-----------|----------|--------|-------------------------|
| event_id  | Yes      | string | ESPN event ID           |
| provider  | No       | string | API provider (default: `espn`) |

**Response (200):**
```json
{
  "game_id": "uuid-string"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/game?event_id=401671769"
```

### Ingest a Week

```
POST /api/ingest/week
```

| Parameter         | Required | Type    | Description                          |
|-------------------|----------|---------|--------------------------------------|
| year              | Yes      | int     | Season year (e.g., 2026)             |
| week              | Yes      | int     | Week number (1-22)                   |
| include_playoffs  | No       | boolean | Include playoffs (default: false)    |
| provider          | No       | string  | API provider (default: `espn`)       |

**Response (200):**
```json
{
  "games_ingested": 16,
  "games_failed": 0
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/week?year=2026&week=1"
```

### Ingest a Season

```
POST /api/ingest/season
```

| Parameter         | Required | Type    | Description                       |
|-------------------|----------|---------|-----------------------------------|
| year              | Yes      | int     | Season year (e.g., 2026)          |
| include_playoffs  | No       | boolean | Include playoffs (default: false) |
| provider          | No       | string  | API provider (default: `espn`)    |

**Response (200):**
```json
{
  "games_ingested": 285,
  "games_failed": 0
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/season?year=2026&include_playoffs=true"
```

## Retrieval API

### Get All Teams

```
GET /api/teams
```

**Response (200):**
```json
[
  {
    "id": "uuid",
    "espn_id": "1",
    "abbr": "KC",
    "full_name": "Kansas City Chiefs"
  },
  ...
]
```

### Get Games (Filtered)

```
GET /api/games
```

| Parameter    | Required | Type   | Description              |
|--------------|----------|--------|--------------------------|
| date_start   | No       | string | Start date (YYYY-MM-DD)  |
| date_end     | No       | string | End date (YYYY-MM-DD)    |
| season       | No       | int    | Filter by season year    |

**Response (200):**
```json
[
  {
    "id": "uuid",
    "espn_id": "401671769",
    "game_date": "2026-09-04T20:20:00-00:00",
    "status_code": "final",
    "week": 1,
    "season_year": 2026,
    "home_abbr": "KC",
    "home_name": "Kansas City Chiefs",
    "away_abbr": "GB",
    "away_name": "Green Bay Packers"
  }
]
```

### Get Game Stats

```
GET /api/stats/game/{game_id}
```

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| game_id   | Yes      | UUID | Game ID     |

**Response (200):** Game summary with both teams' full stats.

### Get Player Stats

```
GET /api/stats/player/{player_id}
```

| Parameter  | Required | Type | Description |
|------------|----------|------|-------------|
| player_id  | Yes      | UUID | Player ID   |

**Response (200):** All player game stats ordered by date (descending).

### Get Team Stats

```
GET /api/stats/team/{team_id}
```

| Parameter | Required | Type | Description |
|-----------|----------|------|-------------|
| team_id   | Yes      | UUID | Team ID     |

**Response (200):** All team game stats ordered by date (descending).

### Get Game Leaderboard

```
GET /api/stats/leaderboard/{game_id}
```

| Parameter | Required | Type   | Description                                  |
|-----------|----------|--------|----------------------------------------------|
| game_id   | Yes      | UUID   | Game ID                                      |
| category  | No       | string | `passing`, `rushing`, or `receiving` (default: passing) |

**Response (200):** Top 20 players in the category, ordered by yards (descending).

### Get Fantasy Stats

```
GET /api/stats/fantasy/{player_id}
```

| Parameter  | Required | Type | Description |
|------------|----------|------|-------------|
| player_id  | Yes      | UUID | Player ID   |

**Response (200):** Player stats with calculated fantasy points and total yards per game.

## Error Responses

| HTTP Code | Meaning              | Example Response                                      |
|-----------|----------------------|-------------------------------------------------------|
| 400       | Bad Request          | `{"detail": "Unknown provider: bad"}`                 |
| 404       | Not Found            | `{"detail": "Game not found: invalid-uuid"}`          |
| 422       | Validation Error     | `{"detail": "week must be between 1 and 22"}`         |
| 500       | Internal Error       | `{"detail": "Database connection failed"}`            |

## CLI Usage

The system also supports direct CLI usage as an alternative to the API:

```bash
# Single game
python -m ingest --game-id 401671769

# All games on a date
python -m ingest --date 2026-09-04

# Specific week
python -m ingest --week 2026 1

# Full season with playoffs
python -m ingest --season 2026 --include-playoffs

# Show table counts
python -m ingest --counts

# Start API server
python -m ingest --service
```

## Architecture

```
                        +-----+----+
                        | Admin UI | (future)
                        +-----+----+
                              |
                              v
                      +-----+----+
                      | FastAPI  |  port 8000
                      | Service  |
                      +-----+----+
                 /         |         \
                /          |          \
   /api/ingest  /   /api/stats  /   /api/teams
              /          |           \
     +-----+--+           +-----+----+
     | Engine           | Retrieval   |
     | (process_game/   | (proc calls)|
     |  process_week/    |             |
     |  process_season)  |             |
     +-----+------------+ +----+------+
             |                    |
   +-----+----+----+      +----+----+----+
   | Provider      |      | DB Writer     |
   | ESPNClient + |----->| callproc ->   |
   | ESPNTransformer|      | stored procs  |
   +-----+---------+      +----+----------+
             |                     |
             +-------+------->----+
                     |
           +---------+--------+
           | PostgreSQL       |
           | tables + procs   |
           +------------------+
```

## Dependency Injection

The API is designed to support multiple data providers. The architecture uses abstract interfaces:

- **APIProvider** — fetches raw data from a sports API
- **Transformer** — normalizes raw data into DB-ready stat dicts
- **DBWriter** — writes data to the database via stored procedures

To add a new provider, implement these three interfaces and pass it to the `IngestionEngine`.

## Database Tables

| Table              | Purpose                         |
|--------------------|---------------------------------|
| game_status        | Game state lookup (seed)        |
| player_position    | Position code lookup (seed)     |
| teams              | Dimension: all teams            |
| players            | Dimension: all players          |
| games              | Dimension: all games            |
| team_game_stats    | Fact: per-team per-game stats   |
| player_game_stats  | Fact: per-player per-game stats |

## Stored Procedures

All writes use stored procedures in `DB/procedures.sql`:
- `usp_seed_game_status()` — seed game states
- `usp_seed_player_position()` — seed position codes
- `usp_upsert_team()` — upsert team
- `usp_upsert_player()` — upsert player
- `usp_upsert_game()` — upsert game
- `usp_upsert_team_game_stats()` — upsert team stats
- `usp_upsert_player_game_stats()` — upsert player stats

See `Documents/StoredProcedures.md` and `Documents/StoredProcedures_Analysis.md` for retrieval procedures.
