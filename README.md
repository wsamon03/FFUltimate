# NFL Ingestion API Documentation

A high-performance, asynchronous API system for ingesting NFL game data from ESPN into a PostgreSQL database.

## Architecture Overview
The ingestion system has been refactored from a synchronous model to an **async-first** architecture.
- **`FastAPI`**: Handles the HTTP API layer.
- **`asyncpg`**: Manages non-blocking database connections via a `ConnectionPool`.
- **`IngestionEngine`**: Orchestrates the pipeline (API Fetch -> Transform -> DB Write).
- **Transactional Integrity**: Ingestions are wrapped in database transactions to prevent dirty data states if a crash occurs mid-process.

## Setup & Installation

### 1. Dependencies
```bash
pip install -r requirements.txt
```
*Note: `celery` and `redis` are included but not currently used by the default router. They can be used later for distributed task processing.*

### 2. Environment Variables
Create a `.env` file at the root of the project to configure your database connection.

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nfl_fantasy
DB_USER=your_db_user
DB_PASSWORD=your_db_password
```

### 3. Database Initialization
The API relies on PostgreSQL stored procedures for efficiency. Ensure your database is seeded before ingesting data:
```sql
CALL usp_seed_game_status();
CALL usp_seed_player_position();
CALL usp_seed_lookup_tables();
```

## Running the API

1. **Start the application:**
   ```bash
   uvicorn ingest.service.app:app --host 0.0.0.0 --port 8000
   ```
2. **Verify startup:** Check your logs for `PostgreSQL Connection Pool ready.`

## API Reference

All ingestion endpoints are asynchronous and return a `task_id` immediately. This allows the server to handle requests without blocking while heavy backend work occurs.

### 1. Ingest a Single Game
Ingests a specific game by its ESPN event ID.
- **URL:** `/api/ingest/game`
- **Method:** `POST`
- **Query Params:** `event_id` (String)

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued"
}
```

### 2. Ingest a Week
Ingests all games for a specific week of a season.
- **URL:** `/api/ingest/week`
- **Method:** `POST`
- **Query Params:**
  - `year` (Integer): The season year.
  - `week` (Integer): The week number (1-22).
  - `include_playoffs` (Boolean, default: False): Set to `True` to include playoff games.

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued"
}
```

### 3. Ingest a Season
Ingests every game for a complete season.
- **URL:** `/api/ingest/season`
- **Method:** `POST`
- **Query Params:**
  - `year` (Integer): The season year.
  - `include_playoffs` (Boolean, default: False): Set to `True` to include playoff games.

**Response:**
```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued"
}
```

### 4. Check Task Status (New)
Monitor the progress and completion of any ingestion task.
- **URL:** `/api/ingest/status/{task_id}`
- **Method:** `GET`
- **Path Params:** `task_id` (UUID)

**Response (Success):**
```json
{
  "status": "completed",
  "progress": {
    "ingested": 50, 
    "failed": 0
  },
  "error": null
}
```

**Response (Failure):**
```json
{
  "status": "failed",
  "progress": {
    "ingested": 48, 
    "failed": 2
  },
  "error": "External API Rate Limit Exceeded"
}
```

## Troubleshooting

- **Connection Pool Errors:** Ensure your `DB_HOST`, `DB_USER`, and `DB_PASSWORD` are correct and allow connections from your server's IP.
- **Missing Data:** If `ingested` remains 0 in the status response, the ESPN API may have returned an empty scoreboard for that week/year combination.
