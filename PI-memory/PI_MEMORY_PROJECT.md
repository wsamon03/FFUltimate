# Pi Memory - Project (FantasyFootball-V2) Knowledge
# Version 1.0 - 2026-06-03

---

## 🎯 Guideline #7: API Versioning & Schema Migrations

**Lesson**:
- `usp_upsert_player_game_stats` has **41 arguments** → easy to mess up during migration
- Use `CREATE OR REPLACE PROCEDURE` with same signature to avoid breaking existing callers
- Always verify parameter count: `SELECT proargnames FROM pg_proc WHERE proname = 'procedure_name';`

**For Projects**: All multi-table stored procedures should maintain compatible signatures to allow seamless upgrades.

---

## 🎯 Lesson #10: Asyncpg `conn.transaction()` Scope

**Lesson**:
- `transaction()` is a **context manager on Connection**, not Pool
- Must follow:
```python
conn = await pool.acquire()
try:
    async with conn.transaction():
        await conn.execute("...")
finally:
    await pool.release(conn)
```
- `async with pool.transaction():` is **invalid syntax** in asyncpg

**For Projects**: Document this pattern in `TRANSACTION_GUIDELINES.md`.

---

## 🎯 Lesson #11: `fetch_game_summary()` can return `None`

**Lesson**:
- ESPN API events can return `None` for games not in the mocked set
- Always check: `if not raw: logger.warning(f"No data for game {event_id}")`
- Use CORS headers explicitly when frontend is not same domain

**For Projects**: All frontend apps should log missing API data → indicates real data bug.

---

## 🎯 Lesson #12: Zero-Dependency Frontend Pattern

**Lesson**:
- **Frontend build pattern**: HTML + Tailwind CDN + Alpine CDN (zero dependencies)
- Run via `http.server` (not `serve` or `vite`)
- Avoid `file://` protocol CORS restrictions

**For Projects**: This is a **reproducible pattern** for any static frontend.

---

## 🎯 Lesson #13: Task Progress Reporting

**Problem**: Task status showed `completed` but progress was `0/0` because background task never started.

**Lesson**:
- Always track `ingested`, `failed`, `total` as **progress counters**
- Include `updated_at` timestamp for task tracking
- Check `task_store.py` (file-based queue) for durability

**For Projects**: All background workers should log progress → enables monitoring/debugging.

---

## 🎯 Lesson #14: Date/Time Parsing in APIs

**Lesson**:
- ESPN API returns strings like `"2024-08-15T00:00:00"`
- Must use `date.fromisoformat()` for Python parsing (not `datetime.strptime`)

**For Projects**: Document parsing patterns in `PARSING_GUIDELINES.md`.

---

## 🎯 Lesson #15: CORS Configuration

**Lesson**:
- Must explicitly allow `["http://localhost:8080", "http://127.0.0.1:8080"]`
- Not allowing `http://localhost` will cause browser errors

**For Projects**: Document CORS patterns in `CORS_GUIDELINES.md`.

---

## 📋 Files Referenced in this Session

| File | Purpose | Status |
|------|---------|--------|
| `ingest/TRANSACTION_GUIDELINES.md` | Asyncpg transaction pattern | ✅ |
| `DB/COALESCE_GUIDELINES.md` | Safe UPDATES pattern | ✅ |
| `BACKEND/MOCK_TESTS_GUIDELINES.md` | Mock vs Real testing | ✅ |
| `BACKEND/POSTGRESQL_SCHEMA_GUIDELINES.md` | Schema migration patterns | ✅ |
| `DEPLOYMENT/clean-service-restart.md` | Service restart pattern | ✅ |
| `restart_services.bat` | Restart script | ✅ |
| `verify_ingestion.py` | Verification script | ✅ |
| `FIXES_SUMMARY.md` | Complete fix summary | ✅ |
| `INGEST/PI_SKILLS/POSTGRESQL_SCHEMA_CHANGES.md` | PostgreSQL upsert skill | ✅ |

---

## ⚠️ Known Issues

| Issue | Status |
|-------|--------|
| MockESPNClient persisted in env | ✅ Fixed |
| COALESCE not applied in stored procedure | ✅ Fixed |
| Task progress misleading | ✅ Fixed with logging |
| Date parsing with ESPN API | ✅ Fixed with fromisoformat |

---

**Last Updated**: 2026-06-03  
**Verified With**: W8/2024 data ingestion, Jameis Winston pass_yds=334 preserved
