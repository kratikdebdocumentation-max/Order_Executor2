@echo off
echo Stopping any running bot processes...
taskkill /f /im python.exe 2>nul
timeout /t 2 /nobreak >nul

echo Starting updated trading bot with pending order management...
python main.py

pause

