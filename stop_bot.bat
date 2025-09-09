@echo off
echo Stopping all Python processes...
taskkill /f /im python.exe
taskkill /f /im pythonw.exe
echo.
echo All Python processes stopped.
echo You can now run the bot again.
pause
