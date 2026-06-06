# COALESCE vs EXCLUDED Updates

## 🎯 The Golden Rule

**For partial stat upserts, use `COALESCE` to preserve existing values!**

### ❌ BUGGY PATTERN: NULL Overwrites Existing Data

When a player has **multiple stat categories** (e.g., QB with passing + rushing stats):
1. First upsert (passing stats): inserts `pass_yds=334, rush_yds=NULL`
2. Second upsert (rushing stats): `INSERT` fails with `ON CONFLICT`, so triggers `UPDATE`
3. **BUT**: `UPDATE` sets `pass_yds = EXCLUDED.pass_yds` → **NULL** (overwrites 334!)
4. Final result: `pass_yds=NULL, rush_yds=10` ❌

```sql
-- ❌ WRONG: Every column uses EXCLUDED
DO UPDATE SET 
    pass_yds       = EXCLUDED.pass_yds,   -- NULL overwrites 334!
    rush_yds       = EXCLUDED.rush_yds,   -- OK
```

### ✅ SAFE PATTERN: Preserve Existing Values

```sql
-- ✅ CORRECT: COALESCE preserves non-NULL existing values
DO UPDATE SET 
    pass_yds       = COALESCE(EXCLUDED.pass_yds, pass_yds),  -- Keeps 334
    rush_yds       = COALESCE(EXCLUDED.rush_yds, rush_yds),  -- Inserts 10
    rec_yds        = COALESCE(EXCLUDED.rec_yds, rec_yds),
    ...
```

### Why This Works

- `COALESCE(EXCLUDED.col, pg.col)` means:
  - If incoming (`EXCLUDED`) value is NOT NULL → use incoming
  - If incoming (`EXCLUDED`) value IS NULL → use existing (`pg`) value
- **Only when ALL values are NULL** → INSERT new row
- **Only when ANY value is NON-NULL** → UPDATE to preserve existing non-NULL

---

## 🧪 Test Case: QB with Pass + Rush Stats

| Call 1 (Passing) | Row After Call 1 |
|------------------|------------------|
| pass_yds=334, rush_yds=NULL | `pass_yds=334, rush_yds=NULL` |

| Call 2 (Rushing) | Row After Call 2 |
|------------------|------------------|
| pass_yds=NULL, rush_yds=10 | `pass_yds=334, rush_yds=10` ✅ (preserved) |
| (without COALESCE?) | `pass_yds=NULL, rush_yds=10` ❌ (overwritten) |

---

## 📋 Full Procedure Schema

`usp_upsert_player_game_stats` has **41 parameters**. Only **metadata** and **last_updated** should use `EXCLUDED`.

| Stat Category | Column Count | Use COALESCE? |
|-----------|------------|-------------|
| Passing | 5 | ✅ |
| Rushing | 4 | ✅ |
| Receiving | 4 | ✅ |
| Defensive | 8 | ✅ |
| Field Goal | 4 | ✅ |
| PAT | 2 | ✅ |
| Metadata | 1 | ❌ (always use EXCLUDED) |
| Last Updated | 1 | ❌ (always use EXCLUDED) |

---

## ⚠️ When NOT to Use COALESCE

- **`metadata`**: Always use `EXCLUDED.metadata` for consistency
- **`last_updated`**: Always use `CURRENT_TIMESTAMP` (no COALESCE)
- **Single-category stats**: COALESCE unnecessary (null won't overwrite anything)

---

## 🧪 Reference

| File | Procedure | Parameters | COALESCE Fields |
|------|----------|-----------|---------------|
| `DB/procedures.sql` | `usp_upsert_player_game_stats` | 41 | 38 fields |
| `ingest/engine.py` | `IngestionEngine.process_game()` | - | Uses `db_writer.upsert_...` |

---

**Last Updated**: 2026-06-03  
**Verified With**: Jameis Winston pass_yds=334 preserved after rush_upsert
