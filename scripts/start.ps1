# Smart CCTV — start MySQL + app
# Run from project root: .\scripts\start.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Join-Path $env:USERPROFILE "Projects\smart-cctv"
Set-Location $ProjectRoot

Write-Host "=== Smart CCTV Startup ===" -ForegroundColor Cyan

# 1. Start MySQL via Docker if available
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Starting MySQL container..." -ForegroundColor Yellow
    docker compose up -d
    Write-Host "Waiting for MySQL health..." -ForegroundColor Yellow
    $maxWait = 60
    $elapsed = 0
    while ($elapsed -lt $maxWait) {
        $status = docker compose ps --format json 2>$null | ConvertFrom-Json -ErrorAction SilentlyContinue
        if ($status -and ($status.Health -eq "healthy" -or $status.State -eq "running")) {
            $portTest = Test-NetConnection -ComputerName localhost -Port 3306 -WarningAction SilentlyContinue
            if ($portTest.TcpTestSucceeded) { break }
        }
        Start-Sleep -Seconds 3
        $elapsed += 3
    }
} else {
    Write-Host "Docker not found. Ensure MySQL is running on localhost:3306" -ForegroundColor Yellow
    Write-Host "  Option A: Install Docker Desktop, then run this script again" -ForegroundColor Gray
    Write-Host "  Option B: Install MySQL Server, run scripts\init_mysql.sql" -ForegroundColor Gray
}

# 2. Start FastAPI
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
& "$ProjectRoot\venv\Scripts\python.exe" "$ProjectRoot\main.py"
