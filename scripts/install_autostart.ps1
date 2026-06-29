# Register Smart CCTV to start at Windows login (Startup folder shortcut, hidden window)
# Run from project root: .\scripts\install_autostart.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$StartScript = Join-Path $ProjectRoot "scripts\start_autostart.ps1"

if (-not (Test-Path $StartScript)) {
    Write-Host "FAIL: start_autostart.ps1 not found." -ForegroundColor Red
    exit 1
}

$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "FAIL: venv not found. Run: python -m venv venv && pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "Smart CCTV.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$StartScript`""
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "Smart CCTV face recognition server"
$Shortcut.Save()

Write-Host ""
Write-Host "Auto-start installed:" -ForegroundColor Green
Write-Host "  $ShortcutPath"
Write-Host ""
Write-Host "The server will start hidden at next login. Logs: logs\autostart.log"
Write-Host "Remove with: .\scripts\uninstall_autostart.ps1"
Write-Host ""
