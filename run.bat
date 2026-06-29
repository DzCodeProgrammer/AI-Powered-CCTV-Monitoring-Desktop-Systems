@echo off
REM Smart CCTV — local run (this PC only)
cd /d "%~dp0"
call venv\Scripts\activate.bat
python main.py
pause
