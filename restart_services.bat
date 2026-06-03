@echo off
setlocal enabledelayedexpansion

echo ========================================
echo FantasyFootball Ingestion Services
echo Starting (Version 2)
echo ========================================
echo.

REM Get list of PIDs to kill BEFORE starting
tasklist /FI "PID eq 132188" /FI "PID eq 130416" ^/FO table
tasklist /FI "PID eq 133012" /FO table
echo.

REM Kill any old API processes (port 8002)
echo Killing old API processes...
wmic PROCESS WHERE "(executename='uvicorn' or COMMANDLINE LIKE '*uvicorn*') AND PID >= 100000" delete
taskkill /F /PID 132188 > nul 2>&1
taskkill /F /PID 133012 > nul 2>&1
taskkill /F /PID 130416 > nul 2>&1
timeout /t 2 /nobreak > nul 2>&1

REM Kill any old Frontend processes (port 8080)
echo Killing old Frontend processes...
wmic PROCESS WHERE "executename='python' AND COMMANDLINE LIKE '*8080*' AND PID >= 100000" delete
taskkill /F /PID 132860 > nul 2>&1
taskkill /F /PID 116284 > nul 2>&1
timeout /t 2 /nobreak > nul 2>&1

REM Verify ports are free
netstat -ano ^| findstr "8002" ^| findstr "LISTEN" > old_api_port.txt
netstat -ano ^| findstr "8080" ^| findstr "LISTEN" > old_frontend_port.txt

echo Starting API Server on port 8002...
start /B C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\start_api.bat
timeout /t 3

REM Verify ports are free
netstat -ano ^| findstr "8002" ^| findstr "LISTEN" 5>nul
netstat -ano ^| findstr "8080" ^| findstr "LISTEN" 5>nul

echo Starting Frontend Server on port 8080...
python -m http.server 8080 > frontend_8080.log 2>&1
start "Frontend Server" cmd /c "timeout /t 2 && echo Ready & pause"

REM Cleanup old port logs
del old_api_port.txt old_frontend_port.txt 2>nul

echo.
echo ========================================
echo Services Started!
echo ========================================
echo API:      http://localhost:8002 (docs at /docs)
echo Frontend: http://localhost:8080 (nflDash)
echo.

echo Press any key to close...
pause
