@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Run setup first: python -m venv venv ^& venv\Scripts\pip install -r requirements.txt -r requirements-desktop.txt
  exit /b 1
)
venv\Scripts\python.exe desktop_main.py
