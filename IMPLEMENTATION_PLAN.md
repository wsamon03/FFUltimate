# NFL Ingestion API - Architectural Implementation Plan

## Status
- [x] Phase 1: Critical Infrastructure Fixes
- [x] Phase 2: API Feature Extensions
- [x] Phase 3: Code Refinements
- [x] Documentation: API Usage Guide Created (`README.md`)

## Phase 1: Critical Infrastructure Fixes

### Step 1: Migrate DB to Async (`asyncpg`)
**Goal:** Replace synchronous `psycopg2` blocking calls with `asyncpg` to prevent blocking the FastAPI event loop during heavy workloads.
**Status:** ✅ Complete
**Changes:** 
- Added `asyncpg` to `requirements.txt`.
- Refactored `PgDBWriter` to use `asyncpg` pool (`create_pool`).
- Changed all DB methods to `async def` using `async with pool.acquire()`.

### Step 2: Implement Transactional Integrity
**Goal:** Prevent dirty data states where some parts of a game insertion succeed while others fail.
**Status:** ✅ Complete
**Changes:**
- Refactored `IngestionEngine` to wrap the entire game ingestion process (Header -> Teams -> Players) inside a single `asyncpg` transaction (`async with self.pool.transaction():`).
- If *any* step fails, the entire operation rolls back.

### Step 3: Decouple Router Dependencies (Dependency Injection)
**Goal:** Stop creating `ESPNClient` and `DBWriter` instances on every API request.
**Status:** ✅ Complete
**Changes:**
- Moved `Pool` initialization to `ingest/service/app.py` startup (`lifespan`).
- The `IngestionEngine` now receives the `Pool` directly in the router.

## Phase 2: API Feature Extensions

### Step 4: Background Task Offloading
**Goal:** Handle long-running "season" ingestions without hanging the API server.
**Status:** ✅ Complete
**Changes:**
- Refactored `ingest_week` and `ingest_season` routers to use `asyncio.create_task` (BackgroundTasks).
- Return a `task_id` immediately upon request.
- Updates `IngestionStatusStore` to reflect progress.

### Step 5: Task Status API Endpoint
**Goal:** Allow the caller to check the progress and completion of a background ingestion.
**Status:** ✅ Complete
**Changes:**
- Created `ingest/service/status_store.py` for tracking task states (`queued`, `running`, `completed`, `failed`).
- Created a `GET /api/ingest/status/{task_id}` endpoint that returns ingestion progress and final `success`/`error` status.

## Phase 3: Code Refinements

### Step 6: Enforce Type Safety & Validation
**Goal:** Eliminate type-mixing issues (e.g., `str` vs `UUID`) in the DB layer.
**Status:** ✅ Complete
**Changes:**
- Refactored `ingest/db_writer.py` to strictly use `uuid.UUID` for all ID-related operations.
- Updated `ingest/engine.py` and `ingest/service/ingestion_router.py` to adhere to strict typing.
- Refactored `ingest/service/status_store.py` to use `uuid.UUID` keys.

## Documentation

### Step 7: API Usage Guide
**Goal:** Provide clear documentation for using the refactored API.
**Status:** ✅ Complete
**Changes:**
- Created `README.md` detailing setup, installation, and endpoint usage (including the new `/status` endpoint).
