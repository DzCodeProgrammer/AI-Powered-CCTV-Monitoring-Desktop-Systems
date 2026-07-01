@echo off
cd /d "%~dp0.."
set "PY=venv\Scripts\python.exe"
if not exist "%PY%" (
  echo venv not found. Run: python -m venv venv ^& venv\Scripts\pip install -r requirements.txt -r requirements-desktop.txt
  exit /b 1
)
echo Installing desktop deps...
"%PY%" -m pip install -q -r requirements-desktop.txt
echo Checking PySide6...
"%PY%" -c "import PySide6; print('PySide6 OK:', PySide6.__file__)"
if errorlevel 1 exit /b 1
echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo Building SmartCCTV.exe (may take 15-30 min)...
"%PY%" -m PyInstaller smart_cctv_desktop.spec --clean
if errorlevel 1 (
  echo BUILD FAILED
  exit /b 1
)
echo.
echo BUILD OK: dist\SmartCCTV\SmartCCTV.exe
echo Copy your .env to dist\SmartCCTV\ before running.
exit /b 0
