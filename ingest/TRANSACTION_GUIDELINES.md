# Transaction Scope Guidelines

## 🎯 The Golden Rule

**`transaction()` is a context manager on CONNECTION, NOT POOL!**

### ✅ CORRECT PATTERN
```python
import asyncpg
from ingest.base import DBWriter

async def process_transaction(pool: asyncpg.Pool):
    conn = await pool.acquire()  # Acquire connection from pool
    try:
        async with conn.transaction():  # Transaction on CONNECTION
            await conn.execute(f"INSERT INTO ...")
            await conn.execute(f"UPDATE ...")
    except Exception:
        # Handle error, re-acquire connection
        raise
    finally:
        await pool.release(conn)  # Return connection to pool
```

### ❌ WRONG PATTERNS

```python
# WRONG: async on POOL.transaction() - pool.transaction() doesn't exist!
async def process_transaction(pool: asyncpg.Pool):
    async with pool.transaction():  # This fails!
        ...

# WRONG: Transaction block, forget to release connection!
async def process_transaction(pool: asyncpg.Pool):
    conn = await pool.acquire()
    async with conn.transaction():
        await conn.execute(...)
    # Forgot to call pool.release(conn)! Connection leaked!
```

---

## 🔍 Why This Pattern?

1. **Transaction Context**: Each `async with conn.transaction()` creates a scoped transaction
2. **Connection Lifecycle**: Must acquire from pool, use transaction, release back
3. **Error Recovery**: If transaction fails, `conn.release()` returns to pool
4. **Pool Integrity**: `asyncpg.Pool` only tracks active connections

---

## 🧪 Additional Guidelines

### Connection Timeout & Health Checks
```python
pool = await asyncpg.create_pool(
    DSN,
    min_size=5,
    max_size=20,
    connection_timeout=20,
    statement_timeout=0,
)

# Always check before using
if not pool:
    raise RuntimeError("Pool not initialized!")
```

### Migration Scripts Need `autocommit=True`
```python
conn = await pool.acquire()
conn.autocommit = True  # Required for single-statement execution
try:
    await conn.execute('CREATE OR REPLACE PROCEDURE ...')
finally:
    conn.autocommit = False
    await pool.release(conn)
```

---

## ⚠️ Common Mistakes

| Mistake | Consequence | Fix |
|---------|--------------|-----|
| `async with pool.transaction()` | `AttributeError` | Use `conn.transaction()` |
| Missing `pool.release(conn)` | Connection leak | Always use `finally` |
| Forget `conn.autocommit=False` | DB errors | Set before migration |

---

## 📋 Reference

| Component | Pattern | Location |
|-----------|---------|----------|
| Correct Usage | `async with conn.transaction()` | `ingest/engine.py:44` |
| Wrong Usage | `async with pool.transaction()` | ❌ Not documented |
| Migration | `conn.autocommit=True` | `DB/procedures.sql` |

---

**Last Updated**: 2026-06-03  
**Verified With**: `usp_upsert_player_game_stats` migration
