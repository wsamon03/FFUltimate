# FantasyFootball Test Suite

Comprehensive test suite for the NFL Fantasy Football data ingestion system. Tests every procedure and API endpoint documented in the `Documents/` folder.

## Test Suite Overview

| File | Category | Covers | Tests |
|------|----------|--------|-------|
| `test_seed_procedures.py` | Procedures | `usp_seed_game_status`, `usp_seed_player_position` | 9 |
| `test_upsert_procedures.py` | Procedures | `usp_upsert_team`, `usp_upsert_player`, `usp_upsert_game`, `usp_upsert_team_game_stats`, `usp_upsert_player_game_stats` | 17 |
| `test_retrieval_procedures.py` | Procedures | 25 retrieval procedures from `StoredProcedures_Retrieval.md` + existence verification | 34+ |
| `test_analysis_procedures.py` | Procedures | 15 analysis procedures from `StoredProcedures_Analysis.md` + existence verification | 27+ |
| `test_api_endpoints.py` | Integration | 7 API endpoints from `API_Documentation.md` + Swagger/OpenAPI spec | 21+ |
| `test_schema.py` | Schema | All 7 tables, 15+ columns, constraints, indexes, all 46 procedures, lookup data | 35+ |
| `test_data_validation.py` | Data | FK integrity, stat plausibility, derived stats, idempotency | 26 |
| `test_espn_comparison.py` | Integration | Live ESPN API vs DB data comparison (Week 1 only, requires internet) | 15+ |

## Prerequisites

- **PostgreSQL** with the NFL FantasyFootball database running
- **Python 3.9+**
- **pytest** (for procedure + schema tests)
- **fastapi** + **httpx** (for API endpoint tests)
- **`requests`** (for ESPN API comparison tests)

### Internet Access (for ESPN tests only)

The `test_espn_comparison.py` suite requires:
- Active internet connection
- Access to `https://site.api.espn.com` endpoints
- No rate limiting from ESPN

### Install dependencies:

```bash
pip install -r ../requirements.txt pytest fastapi httpx requests
```

## Database Setup

Before running tests, ensure your database schema is deployed:

```bash
# Create the database and deploy schema
python ../DB/create_db.py

# Deploy stored procedures
psql -d nfl_fantasy -f ../DB/procedures.sql
psql -d nfl_fantasy -f ../DB/procedures_retrieval.sql
psql -d nfl_fantasy -f ../DB/procedures_analysis.sql
```

## Quick Start

### Run all test suites:
```bash
python test_runner.py
```

### Run individual suites:
```bash
# Schema only (table/column/constraint verification)
python test_runner.py --schema

# All procedure tests (seed + upsert + retrieval + analysis)
python test_runner.py --procedures

# API endpoint tests
python test_runner.py --api

# Data validation tests
python test_runner.py --data
```

### Run directly with pytest:
```bash
# All tests
pytest -v

# Single test file
pytest test_schema.py -v
pytest test_seed_procedures.py -v
pytest test_upsert_procedures.py -v
pytest test_retrieval_procedures.py -v
pytest test_analysis_procedures.py -v
pytest test_api_endpoints.py -v
pytest test_data_validation.py -v

# Specific test class
pytest test_seed_procedures.py::TestSeedGameStatus -v

# Specific test method
pytest test_upsert_procedures.py::TestUpsertTeam::test_insert_new_team -v
```

### List available tests:
```bash
python test_runner.py --list
```

## What Each Suite Tests

### Schema Tests (`test_schema.py`)
- **Table existence**: All 7 tables from `schema.sql`
- **Column verification**: Every column name, type, and nullable constraint
- **Unique constraints**: On `espn_id`, `abbr`, `(game_id, team_id)`, `(player_id, game_id)`
- **Indexes**: All documented indexes on ESPN IDs, dates, and foreign keys
- **Procedure existence**: All 46 documented procedures
- **Lookup data**: `game_status` and `player_position` tables seeded

### Seed Procedure Tests (`test_seed_procedures.py`)
- `usp_seed_game_status()`: Inserts 3 statuses, idempotent, unique constraint
- `usp_seed_player_position()`: Inserts 12+ positions, idempotent, all have descriptions

### Upsert Procedure Tests (`test_upsert_procedures.py`)
- **Insert new records**: Each procedure creates new data
- **Update existing**: Upsert overwrites when key exists
- **Unique constraints**: Duplicate inserts raise `UniqueViolation`
- **Special cases**: Decimal sacks, JSONB metadata, null stats

### Retrieval Procedure Tests (`test_retrieval_procedures.py`)
- **Existence**: All 25 documented procedures found in database
- **Functionality**: Each procedure returns expected data
- **Filtering**: Date ranges, ESPN IDs, team/player lookups work correctly
- **Analysis**: Top passers/rushers/receivers, game summary, scoring leaders

### Analysis Procedure Tests (`test_analysis_procedures.py`)
- **Existence**: All 15 documented analysis procedures found
- **Player procedures**: Game complete, season, week-by-week, career
- **Team procedures**: Season complete, week-by-week, career, vs opponent
- **Leaderboards**: Passing, rushing, receiving leaders
- **Fantasy stats**: Calculated fantasy points and total yards

### Data Validation Tests (`test_data_validation.py`)
- **FK integrity**: No orphaned records in any foreign key relationship
- **Stat plausibility**: No negative yards, TDs, or attempts; comp <= att
- **Derived stats**: Quarter scores sum to total
- **Idempotency**: Upsert procedures produce no duplicates when called multiple times

### ESPN API Comparison Tests (`test_espn_comparison.py`)
- **Game-level data**: Scores, dates, status, team IDs vs ESPN
- **Player stats**: Passing, rushing, receiving, defensive stats comparison
- **Team stats**: Yards, first downs, other boxscore stats
- **Leaderboards**: Top passers/rushers/receivers validation
- **Network resilience**: Handles API failures, timeouts, and rate limits gracefully
- **Requirements**: Internet access, ESPN API availability

### API Endpoint Tests (`test_api_endpoints.py`)
- **Ingestion**: POST /api/ingest/game, /week, /season (mocked engine)
- **Retrieval**: GET /api/teams, /games, /stats/* endpoints (mocked DB)
- **Error responses**: 400, 404, 422 status codes
- **Swagger**: /docs and /openapi.json available
- **Fantasy formula**: Yards/10 + TD*4 + rec*0.5

### Data Validation Tests (`test_data_validation.py`)
- **FK integrity**: No orphaned records in any foreign key relationship
- **Stat plausibility**: No negative yards, TDs, or attempts; comp <= att
- **Derived stats**: Quarter scores sum to total
- **Idempotency**: Upsert procedures produce no duplicates when called multiple times

## Architecture

```
Testing/
  conftest.py              # Shared fixtures (db connection, test data)
  test_schema.py           # Schema integrity (tables, columns, constraints, indexes)
  test_seed_procedures.py  # Seed procedure unit tests
  test_upsert_procedures.py # Upsert procedure unit tests
  test_retrieval_procedures.py # Retrieval procedure tests
  test_analysis_procedures.py # Analysis procedure tests
  test_api_endpoints.py    # FastAPI endpoint integration tests
  test_data_validation.py  # Data validation & business rules
  test_runner.py           # Unified CLI test runner
  README.md                # This file
```

## Mapping Documentation to Tests

| Documentation File | Test Coverage |
|---|---|
| `API_Documentation.md` | `test_api_endpoints.py` |
| `StoredProcedures.md` | `test_seed_procedures.py`, `test_upsert_procedures.py` |
| `StoredProcedures_Retrieval.md` | `test_retrieval_procedures.py` |
| `StoredProcedures_Analysis.md` | `test_analysis_procedures.py` |
| `schema.sql` | `test_schema.py` |
| Business rules | `test_data_validation.py` |
