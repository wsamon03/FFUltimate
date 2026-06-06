# POSTGRESQL_SCHEMA_CHANGES Skill

**Skill ID**: `POSTGRESQL_SCHEMA_CHANGES`  
**Type**: Development  
**Difficulty**: Medium

---

## 🎯 What This Skill Does

This skill implements the ability to **re-create any PostgreSQL stored procedure from a Python script**, useful when:

1. Procedures are **too large** for CLI `psql` editing
2. Procedures have **41+ parameters** (e.g., `usp_upsert_player_game_stats`)
3. Need **atomic modifications** without manual schema dumps
4. Want to **avoid CLI complexity**

---

## 🔧 Implementation

### Python Code

```python
import psycopg2
import re
from typing import List

def create_or_update_procedure(
    db_host: str,
    db_port: int,
    db_name: str,
    db_user: str,
    db_password: str,
    proc_name: str,
    proc_sql: str
) -> List[int]:
    """
    Re-create/upsert a stored procedure from file content.
    
    Requirements:
    - proc_name: e.g., "usp_upsert_player_game_stats"
    - proc_sql: Full CREATE OR REPLACE PROCEDURE statement (multi-line)
    - Returns: Number of rows affected (1 or 0)
    """
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
    )
    conn.autocommit = True  # Required for single statement execution
    try:
        cur = conn.cursor()
        
        # Check if procedure exists
        cur.execute(
            'SELECT proname FROM pg_proc WHERE proname = %s',
            (proc_name,)
        )
        if cur.fetchone() is None:
            log(f"Procedure '{proc_name}' does not exist. Creating...")
        else:
            log(f"Procedure '{proc_name}' exists. Updating...")
        
        # Execute procedure definition
        cur.execute(proc_sql)
        
        return 1  # Success
    except Exception as e:
        log(f"Error creating proc '{proc_name}': {e}")
        return 0
    finally:
        conn.autocommit = False
        cur.close()
        conn.close()

def load_and_update_procedure(
    db_config: Dict[str, any],
    proc_name: str,
    proc_file: str
) -> int:
    """
    Load procedure from file and update.
    
    Args:
        proc_file: Path to .sql file containing procedure
        
    Returns:
        Number of rows affected (1 or 0)
    """
    with open(proc_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find single procedure
    pattern = r'CREATE OR REPLACE PROCEDURE (\w+)\(.{3,}\n(\s+\$.+?){10,}'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        proc_name = match.group(1)
        proc_sql = match.group(2)
        
        return create_or_update_procedure(**db_config, proc_name, proc_sql)
    
    log(f"Could not find '{proc_name}' in file '{proc_file}'")
    return 0
```

### Usage Example

```python
from ingest.utils.db_migration import load_and_update_procedure

# Load procedure from file
with open('/Path/to/DB/procedures.sql', encoding='utf-8') as f:
    content = f.read()

# Find usp_upsert_player_game_stats
pattern = r'(CREATE OR REPLACE PROCEDURE usp_upsert_player_game_stats\(\n.*?)$'
match = re.search(pattern, content, re.DOTALL)
if match:
    proc_name = 'usp_upsert_player_game_stats'
    proc_sql = match.group(1)
    
    # Update procedure in DB
    result = create_or_update_procedure(
        db_host='localhost',
        db_port=5432,
        db_name='nfl_fantasy',
        db_user='postgres',
        db_password='...',
        proc_name=proc_name,
        proc_sql=proc_sql
    )
    
    log(f"Procedure updated: {'success' if result == 1 else 'failed'}")
```

---

## ⚠️ Important Notes

### Parameter Count Must Match

Before executing, **verify parameter count**:

```sql
-- ✅ ALWAYS VERIFY
SELECT proname, pronargs FROM pg_proc WHERE proname = 'proc_name';
```

If `pronargs` doesn't match your new definition → **FAILS**.

### Large Procedure Limitation

Some PostgreSQL versions **limit procedure definition size** (e.g., 1024 lines). For larger:
1. Use **multiple CREATE statements**
2. Wrap in **CREATE FUNCTION** instead

---

## 🧪 Testing

```bash
# Test the skill
./test_pg_schema_skill.py

# Expected output:
# Created/Updated: usp_upsert_player_game_stats
# Result: success
```

---

## 📋 Related Skills

- `TRANSACTION_SCOPE` - Connection management
- `ASYNC_PG_PATTERN` - Async database operations
- `POSTGRESQL_COALESCE` - Safe UPDATE patterns

---

**Skill Added**: 2026-06-03  
**Verified With**: `usp_upsert_player_game_stats` COALESCE migration
