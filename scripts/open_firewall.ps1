# Allow inbound TCP on Smart CCTV port (run PowerShell as Administrator)
# Usage: .\scripts\open_firewall.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$port = 8000

if (Test-Path "$ProjectRoot\.env") {
    $match = Select-String -Path "$ProjectRoot\.env" -Pattern '^\s*PORT\s*=\s*(\d+)' | Select-Object -First 1
    if ($match) { $port = [int]$match.Matches.Groups[1].Value }
}

$ruleName = "Smart CCTV Port $port"

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Firewall rule already exists: $ruleName" -ForegroundColor Yellow
} else {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow `
        -Protocol TCP -LocalPort $port | Out-Null
    Write-Host "Created firewall rule: $ruleName (TCP $port inbound)" -ForegroundColor Green
}

Write-Host "Other devices on your LAN can connect to http://<your-ip>:$port/login"
