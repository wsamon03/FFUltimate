# FantasyFootball Database Setup Script for Windows
# Run as Administrator or with appropriate permissions
#
# Prerequisites:
#   1. Install PostgreSQL
#   2. Start the PostgreSQL service
#   3. Run: Enable-PgAdminConnection (optional, for pgAdmin GUI)

param(
    [string]$Host = "localhost",
    [string]$Port = "5432",
    [string]$DatabaseName = "fantasyfootball",
    [string]$Username = "postgres",
    [string]$Password = ""
)

# Ensure psql is in PATH
Write-Host "=== FantasyFootball Database Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check for PostgreSQL
$psql = Get-Command -Name psql -ErrorAction SilentlyContinue
if ($null -eq $psql) {
    Write-Host "ERROR: psql not found in PATH" -ForegroundColor Red
    Write-Host "Please add PostgreSQL bin directory to PATH or use full path" -ForegroundColor Red
    Write-Host "Example: psql = 'C:\Program Files\PostgreSQL\<version>\bin\psql.exe'" -ForegroundColor Red
    exit 1
}

# Check if database exists
Write-Host "Checking for database '$DatabaseName'..." -ForegroundColor Yellow
try {
    $test = & $psql.Source "-h $Host -p $Port -U $Username -lqt" 2>&1 | Select-String -Quiet $DatabaseName
    if ($test) {
        Write-Host "  Database '$DatabaseName' already exists" -ForegroundColor Green
    } else {
        Write-Host "  Creating database '$DatabaseName'..." -ForegroundColor Yellow
        & $psql.Source "-h $Host -p $Port -U $Username -c `\"CREATE DATABASE $DatabaseName;\"" 2>&1
        Write-Host "  Database created successfully" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Connect to database and run setup
Write-Host ""
Write-Host "Connecting to database..." -ForegroundColor Yellow
Write-Host ""

try {
    & $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -f 'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\DB\schema.sql'"
    Write-Host ""
    Write-Host "Tables created successfully" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Seed lookup tables
Write-Host "Seeding lookup tables..." -ForegroundColor Yellow
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -c `\"CREATE OR REPLACE FUNCTION seed_game_status() RETURNS void AS \\\$\$ BEGIN INSERT INTO game_status (status_code, description) VALUES ('scheduled', 'Game has not started'), ('live', 'Game is in progress'), ('final', 'Game is complete') ON CONFLICT (status_code) DO NOTHING; END; \\\$\$ LANGUAGE plpgsql; SELECT seed_game_status();\\\""`" 2>&1
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -c `\"CREATE OR REPLACE FUNCTION seed_player_position() RETURNS void AS \\\$\$ BEGIN INSERT INTO player_position (position_code, description) VALUES ('QB', 'Quarterback'), ('RB', 'Running Back'), ('WR', 'Wide Receiver'), ('TE', 'Tight End'), ('K', 'Kicker'), ('DL', 'Defensive Lineman'), ('LB', 'Linebacker'), ('CB', 'Cornerback'), ('S', 'Safety'), ('DP', 'Defensive Player'), ('P', 'Punter'), ('HS', 'Defensive Specialist') ON CONFLICT (position_code) DO NOTHING; END; \\\$\$ LANGUAGE plpgsql; SELECT seed_player_position();\\\""`" 2>&1
Write-Host ""

# Load upsert procedures
Write-Host "Loading upsert stored procedures..." -ForegroundColor Yellow
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -f 'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\DB\procedures.sql'" 2>&1
Write-Host ""

# Load retrieval procedures
Write-Host "Loading retrieval stored procedures..." -ForegroundColor Yellow
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -f 'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\DB\procedures_retrieval.sql'" 2>&1
Write-Host ""

# Load analysis procedures
Write-Host "Loading analysis stored procedures..." -ForegroundColor Yellow
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -f 'C:\Users\qabct\Documents\Programming\FantasyFootball\Version2\DB\procedures_analysis.sql'" 2>&1
Write-Host ""

# Verify
Write-Host "Verifying setup..." -ForegroundColor Yellow
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -c `\"SELECT tablename FROM pg_tables ORDER BY tablename;\\\""`" 2>&1
Write-Host ""
& $psql.Source "-h $Host -p $Port -U $Username -d $DatabaseName -c `\"SELECT proname FROM pg_proc WHERE pronamespace::regnamespace = 'public' ORDER BY proname LIMIT 20;\\\""`" 2>&1
Write-Host ""

Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Call: CALL usp_seed_game_status();" -ForegroundColor White
Write-Host "  2. Call: CALL usp_seed_player_position();" -ForegroundColor White
Write-Host "  3. Begin inserting data using upsert procedures" -ForegroundColor White
