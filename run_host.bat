@echo off
REM Smart CCTV — LAN host (accessible from other devices on same network)
cd /d "%~dp0"
set HOST=0.0.0.0
call venv\Scripts\activate.bat
python main.py
pause
