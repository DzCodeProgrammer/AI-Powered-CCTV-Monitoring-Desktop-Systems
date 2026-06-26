# Smart CCTV — host on LAN (0.0.0.0) so phones/tablets/PCs on same Wi‑Fi can access
# Run from project root: .\scripts\start_host.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "FAIL: venv not found. Run: python -m venv venv && pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "=== Smart CCTV Host Mode (LAN) ===" -ForegroundColor Cyan

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Host "Starting MySQL container..." -ForegroundColor Yellow
    docker compose up -d
    Start-Sleep -Seconds 5
} else {
    Write-Host "Docker not found — ensure MySQL is on localhost:3306" -ForegroundColor Yellow
}

& $Python "$ProjectRoot\scripts\migrate_schema.py" | Out-Null

# Bind all interfaces — override .env for this session
$env:HOST = "0.0.0.0"

$port = 8000
if (Test-Path "$ProjectRoot\.env") {
    $match = Select-String -Path "$ProjectRoot\.env" -Pattern '^\s*PORT\s*=\s*(\d+)' | Select-Object -First 1
    if ($match) { $port = [int]$match.Matches.Groups[1].Value }
}

Write-Host ""
Write-Host "Hosting on 0.0.0.0:$port — other devices use your PC's LAN IP (shown after startup)." -ForegroundColor Green
Write-Host "If blocked, run as Administrator: .\scripts\open_firewall.ps1" -ForegroundColor Gray
Write-Host ""

& $Python "$ProjectRoot\main.py"
