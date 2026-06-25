#Requires -Version 5.1
# Apply MySQL passwords from .env (run after generate_secrets.py)

$ErrorActionPreference = "Stop"
$ProjectRoot = Join-Path $env:USERPROFILE "Projects\smart-cctv"
Set-Location $ProjectRoot

function Get-EnvValue([string]$Key) {
    $line = Get-Content ".env" | Where-Object { $_ -match "^\s*$Key=" } | Select-Object -First 1
    if (-not $line) { throw "Missing $Key in .env" }
    return ($line -split "=", 2)[1].Trim()
}

$dbUser = Get-EnvValue "DB_USER"
$dbPass = Get-EnvValue "DB_PASSWORD"
$rootPass = Get-EnvValue "MYSQL_ROOT_PASSWORD"

$mysql = Get-Command mysql -ErrorAction SilentlyContinue
if (-not $mysql) {
    $candidates = @(
        "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe",
        "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { $mysql = $path; break }
    }
}
if (-not $mysql) { throw "mysql client not found" }
if ($mysql -is [System.Management.Automation.ApplicationInfo]) { $mysql = $mysql.Source }

Write-Host "Securing MySQL users..." -ForegroundColor Cyan

# Try root without password first (fresh install), then with password from .env
$rootArgs = @("-u", "root", "-e", "SELECT 1")
& $mysql @rootArgs 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $rootArgs = @("-u", "root", "-p$rootPass", "-e", "SELECT 1")
    & $mysql @rootArgs 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Cannot connect as root. Set root password manually first." }
    $auth = @("-u", "root", "-p$rootPass")
} else {
    $auth = @("-u", "root")
}

$sql = @"
ALTER USER 'root'@'localhost' IDENTIFIED BY '$rootPass';
CREATE USER IF NOT EXISTS '$dbUser'@'localhost' IDENTIFIED BY '$dbPass';
CREATE USER IF NOT EXISTS '$dbUser'@'%' IDENTIFIED BY '$dbPass';
ALTER USER '$dbUser'@'localhost' IDENTIFIED BY '$dbPass';
ALTER USER '$dbUser'@'%' IDENTIFIED BY '$dbPass';
GRANT ALL PRIVILEGES ON smart_cctv.* TO '$dbUser'@'localhost';
GRANT ALL PRIVILEGES ON smart_cctv.* TO '$dbUser'@'%';
FLUSH PRIVILEGES;
"@

$sql | & $mysql @auth
if ($LASTEXITCODE -ne 0) { throw "Failed to apply MySQL security settings" }

Write-Host "MySQL secured: root + $dbUser passwords updated." -ForegroundColor Green
