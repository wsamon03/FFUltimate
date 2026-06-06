# Kill all processes on ports 8000 and 8001
$ports = @(8000, 8001)

foreach ($port in $ports) {
    $pids = @(netstat -ano | findstr ":$port.*LISTENING" | ForEach-Object { ($_ -split '\s+')[-1] } | Where-Object { $_ -match '^\d+$' })
    foreach ($pid in $pids) {
        try {
            Write-Host "Killing $pid on port $port"
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host "Could not kill $pid"
        }
    }
}

Start-Sleep -Seconds 2

Write-Host "="
Write-Host "Starting Backend on port 8001"
Write-Host "="

# Start backend
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "ingest.service.app:app", "--host", "127.0.0.1", "--port", "8002" -WorkingDirectory "C:/Users/qabct/Documents/Programming/FantasyFootball/Version2" -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "="
Write-Host "Starting Frontend on port 8000"
Write-Host "="

# Start frontend HTTP server
Start-Process -FilePath "python" -ArgumentList "C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/ingest/frontend/server.py" -WorkingDirectory "C:/Users/qabct/Documents/Programming/FantasyFootball/Version2/ingest" -WindowStyle Normal

Write-Host "="
Write-Host "Services started!"
Write-Host "Frontend: http://localhost:8000"
Write-Host "Backend:  http://localhost:8002"
Write-Host "="

# Quick test
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 3
    Write-Host "Frontend responds: YES"
    Write-Host "Content: $($response.StatusCode)"
} catch {
    Write-Host "Frontend test failed: $($_.Exception.Message)"
}

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8002/api/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "Backend responds: YES"
} catch {
    $response = Invoke-RestMethod -Uri "http://localhost:8002/api/teams" -TimeoutSec 3
    Write-Host "Backend responds: YES"
}
