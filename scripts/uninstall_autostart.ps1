# Remove Smart CCTV from Windows Startup
# Run from project root: .\scripts\uninstall_autostart.ps1

$Startup = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $Startup "Smart CCTV.lnk"

if (Test-Path $ShortcutPath) {
    Remove-Item -Path $ShortcutPath -Force
    Write-Host "Removed auto-start shortcut: $ShortcutPath" -ForegroundColor Green
} else {
    Write-Host "No Smart CCTV startup shortcut found." -ForegroundColor Yellow
}
