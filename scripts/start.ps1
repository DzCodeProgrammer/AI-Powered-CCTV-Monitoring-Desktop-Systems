# Smart CCTV — start MySQL + app (localhost only)
# Run from project root: .\scripts\start.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "FAIL: venv not found. Run: python -m venv venv && pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "=== Smart CCTV Startup (local) ===" -ForegroundColor Cyan

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Starting MySQL container..." -ForegroundColor Yellow
    docker compose up -d
    Start-Sleep -Seconds 5
} else {
    Write-Host "Docker not found — ensure MySQL is on localhost:3306" -ForegroundColor Yellow
}

& $Python "$ProjectRoot\scripts\migrate_schema.py" | Out-Null

Write-Host "Starting server on 127.0.0.1 (see .env for PORT)..." -ForegroundColor Yellow
& $Python "$ProjectRoot\main.py"
