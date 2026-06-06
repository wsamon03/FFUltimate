# PostgreSQL Schema Changes Guidelines

## 🎯 Guideline #1: Verify Parameter Count FIRST

Before re-creating a stored procedure, **verify the parameter count matches**:

```sql
-- ✅ VERIFY PARAMETER COUNT FIRST
SELECT proargnames FROM pg_proc WHERE proname = 'usp_upsert_player_game_stats';
-- Output should return 41 parameters ($1...$41)

-- ❌ WRONG: Assume parameter count from old procedure
CREATE OR REPLACE PROCEDURE usp_upsert_player_game_stats(
    -- Only 39 parameters! This will fail!
    p_player_id      UUID,
    p_game_id        UUID,
    ...
    -- Missing p_p_long, p_metadata
)
```

**Critical**: `SELECT proargnames` shows all 41 parameter names exactly.

---

## 🐍 Guideline #2: Create from Python File, Not CLI

Some procedures are **too large** or **contain dynamic logic** for `psql` CLI. Use Python instead:

### ✅ Python Pattern
```python
import psycopg2
import re

def create_or_update_procedure(conn, proc_name, proc_sql):
    """Re-create stored procedure from file."""
    cur = conn.cursor()
    
    # Verify procedure exists
    cur.execute(
        'SELECT proname FROM pg_proc WHERE proname = %s',
        (proc_name,)
    )
    if cur.fetchone() is None:
        cur.execute(f"CREATE OR REPLACE PROCEDURE {proc_name}")
    else:
        cur.execute(f"ALTER PROCEDURE {proc_name}")
    
    # Execute procedure definition
    # For multi-statement procedures, use autocommit
    conn.autocommit = True
    try:
        cur.execute(f"{proc_sql}")
    finally:
        conn.autocommit = False
        cur.close()

# Create procedure from file
with open('DB/procedures.sql') as f:
    content = f.read()
    
# Extract usp_upsert_player_game_stats
pattern = r'(CREATE OR REPLACE PROCEDURE [^\];]+CREATE OR REPLACE PROCEDURE)'
match = re.search(pattern, content, re.DOTALL)
if match:
    create_or_update_procedure(conn, 'usp_upsert_player_game_stats', match.group(1))
```

### ⚠️ Why This Is Useful

1. **Multi-line CREATE** statements often exceed CLI limits
2. **Complex procedures** (41+ params) are harder to manually edit in CLI
3. **Large procedures** (1500+ lines) can't be pasted efficiently
4. **Better error handling** with Python's try/except

---

## 📋 Guideline #3: Maintain Signature Compatibility

When modifying a **multi-column procedure** (like player_game_stats with 41 params):

```sql
-- ✅ CORRECT: Same signature, different definition
CREATE OR REPLACE PROCEDURE usp_upsert_player_game_stats(
    p_player_id      UUID,
    p_game_id        UUID,
    p_pass_comp      INT,        -- Same signature → existing callers still work
    p_pass_att       INT,
    ...
    -- Same 41 parameters
    p_metadata       JSONB
)
```

---

## 🧪 Guideline #4: Test Changes on Development DB First

```sql
-- ❌ WRONG: Modify on production, test on staging
-- ❌ Can't easily roll back

-- ✅ CORRECT: 
-- 1. Copy production schema to local dev
-- 2. Test changes on dev
-- 3. Apply to production
```

---

## 📋 Guideline #5: Log Procedure Changes

```bash
# Log each procedure change
echo "Created: $($date '+%Y-%m-%d %H:%M:%S')" >> db_migrations.log
echo "Procedure: usp_upsert_player_game_stats" >> db_migrations.log
echo "Parameter count: $(pg_column_count)" >> db_migrations.log
echo "Changes: COALESCE added for 38 fields" >> db_migrations.log
```

---

## 📝 Guidelines Summary

| # | Guideline | Priority |
|---|----------|--------|
| 1 | Verify parameter count | 🔴 HIGH |
| 2 | Use Python for large procedures | 🟡 MEDIUM |
| 3 | Maintain signature compatibility | 🔴 HIGH |
| 4 | Test on dev before prod | 🟡 MEDIUM |
| 5 | Log all changes | 🟢 LOW |

---

**Last Updated**: 2026-06-03  
**Verified With**: `usp_upsert_player_game_stats` 41-parameter procedure
