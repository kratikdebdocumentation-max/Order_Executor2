@echo off
echo Starting fresh...
echo.

REM Clear Python cache
if exist __pycache__ rmdir /s /q __pycache__
if exist *.pyc del /q *.pyc

REM Clear any temp files
if exist *.tmp del /q *.tmp
if exist *.log del /q *.log

echo.
echo ✅ Fresh start complete!
echo.
echo Your project is now clean and ready to use.
echo.
echo To run your bot:
echo   .venv\Scripts\python.exe main.py
echo.
pause

