# Clean Service Restart Guidelines

## 🎯 Why This Matters

**Problem**: Long-running services (uvicorn, http.server) can become "zombie" processes that:
1. Hold memory
2. Ignore restart signals
3. Port conflicts cause new service to fail
4. Database connection leaks

**Solution**: Always kill old instances **before** starting new ones.

---

## 🔍 Guideline #1: List PIDs to Confirm Before Killing

```bash
# ✅ GOOD: See what you're going to kill
tasklist /FI "PID eq 132188" /FO table
# Output:
PID    SESSION    NAME          IMM            STATE
132188      1 uvicorn.exe  64-bit
```

**Never kill without confirmation!**

---

## ⚡ Guideline #2: Use WMI or Taskkill for Clean Shutdown

### Method A: WMI (Recommended)
```bat
REM Delete all uvicorn processes >= 100000 pid
wmic PROCESS WHERE "executename='uvicorn' AND PID >= 100000" delete
```

**Advantage**: Deletion happens atomically (all or nothing)

### Method B: Taskkill by PID
```bat
REM Kill specific PIDs by PID
taskkill /F /PID 132188
taskkill /F /PID 133012
```

**Advantage**: Works with any service name, not just uvicorn

---

## ⏱️ Guideline #3: Add Timeout for Graceful Shutdown

**Why**: uvicorn's thread pool needs time to drain before killing.

```bat
REM Give uvicorn 2 seconds to shut down gracefully
timeout /t 2 /nobreak > nul 2>&1
```

**Without This**: uvicorn might exit abruptly → connection pool still has active connections!

---

## 🔄 Guideline #4: Verify Ports Are Free

**Problem**: "Port already in use" despite killing service.

**Why**: Service might hold orphaned port after crash but before Python GC finishes.

```bat
REM Check for LISTENING ports
netstat -ano ^| findstr "8002" ^| findstr "LISTEN"
# Output:
TCP    0.0.0.0:8002           0.0.0.0:0              LISTENING       132188

REM Check for LISTENING ports after kill
netstat -ano ^| findstr "8002" ^| findstr "LISTEN" >nul
# Expected (no output):
# (no output means port is free)
```

---

## 🚀 Guideline #5: Verify Startup

```bat
REM Start uvicorn (port 8002)
uvicorn ingest.service.app:app --host 0.0.0.0 --port 8002

REM Verify ports are free after starting
netstat -ano ^| findstr "8002" ^| findstr "LISTEN"
# Output should show new PID
TCP    0.0.0.0:8002           0.0.0.0:0              LISTENING       132456

REM Test endpoint
curl http://localhost:8002/docs
```

---

## 🎞️ Full Restart Script Pattern

```bat
@echo off
setlocal

echo === Restart Services ===

REM Step 1: Confirm what's running
tasklist /FI "PID eq <PID>" ^/FO table

REM Step 2: Kill old processes
wmic PROCESS WHERE "executename='uvicorn' OR PID >= 100000" delete
timeout /t 2 /nobreak  -- Graceful shutdown

REM Step 3: Verify port free
netstat -ano ^| findstr "8002" ^| findstr "LISTEN" >nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Port 8002 still in use!
    pause
    exit /b 1
)

REM Step 4: Kill frontend
taskkill /F /PID <FRONTEND_PID>
timeout /t 2 /nobreak

REM Step 5: Verify frontend port free
netstat -ano ^| findstr "8080" ^| findstr "LISTEN" >nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Port 8080 still in use!
    exit /b 1
)

REM Step 6: Start new instances
uvicorn ingest.service.app:app --host 0.0.0.0 --port 8002
python -m http.server 8080 > frontend.log 2>&1

echo === Restart Complete ===
echo API: http://localhost:8002
echo Frontend: http://localhost:8080
pause
```

---

## 📋 Guidelines Summary

| # | Guideline | Priority |
|---|----------|--------|
| 1 | List PIDs before killing | 🔴 HIGH |
| 2 | Use WMI or Taskkill | 🔴 HIGH |
| 3 | Add 2-second timeout | 🟡 MEDIUM |
| 4 | Verify ports free | 🔴 HIGH |
| 5 | Verify startup | 🟡 MEDIUM |

---

## ✅ For All Services

These guidelines should be **standardized**:

- **Frontend**: All `python -m http.server` commands
- **API**: All `uvicorn` commands
- **Workers**: `celery-beat`, `redis-server`, etc.
- **Database**: Migration scripts with `CREATE OR REPLACE`

**One script per service**: `restart_frontend.bat`, `restart_api.bat`

---

**Last Updated**: 2026-06-03  
**Used With**: `restart_services.bat`
