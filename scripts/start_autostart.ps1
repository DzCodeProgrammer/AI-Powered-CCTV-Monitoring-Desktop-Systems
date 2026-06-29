# Smart CCTV — background startup (Windows auto-start, no visible terminal)
# Called by install_autostart.ps1; logs to logs/autostart.log

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "autostart.log"

function Write-Log([string]$Message) {
    if (-not (Test-Path $LogDir)) {
        New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    }
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

if (-not (Test-Path $Python)) {
    Write-Log "FAIL: venv not found at $Python"
    exit 1
}

Write-Log "=== Smart CCTV auto-start ==="

$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
    Write-Log "Starting MySQL container..."
    try {
        docker compose up -d 2>&1 | ForEach-Object { Write-Log $_ }
        Start-Sleep -Seconds 5
    } catch {
        Write-Log "Docker start failed: $_"
    }
} else {
    Write-Log "Docker not found — ensure MySQL is on localhost:3306"
}

try {
    & $Python "$ProjectRoot\scripts\migrate_schema.py" 2>&1 | ForEach-Object { Write-Log $_ }
} catch {
    Write-Log "migrate_schema failed: $_"
}

Write-Log "Starting server (see .env for HOST/PORT)..."
try {
    & $Python "$ProjectRoot\main.py" *>> $LogFile 2>&1
} catch {
    Write-Log "Server exited: $_"
    exit 1
}
