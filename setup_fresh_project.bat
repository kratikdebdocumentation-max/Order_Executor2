@echo off
echo Creating fresh project...
echo.

REM Create new project directory
set NEW_PROJECT=C:\Users\krati\PycharmProjects\Order_Executor_Fresh
mkdir "%NEW_PROJECT%"

REM Copy essential files
copy main.py "%NEW_PROJECT%\"
copy config.py "%NEW_PROJECT%\"
copy api_client.py "%NEW_PROJECT%\"
copy trading_engine.py "%NEW_PROJECT%\"
copy telegram_bot.py "%NEW_PROJECT%\"
copy websocket_handler.py "%NEW_PROJECT%\"
copy trade_logger.py "%NEW_PROJECT%\"
copy utils.py "%NEW_PROJECT%\"
copy api_helper.py "%NEW_PROJECT%\"
copy requirements.txt "%NEW_PROJECT%\"
copy credentials.json "%NEW_PROJECT%\"
copy NorenRestApiPy-0.0.22-py2.py3-none-any.whl "%NEW_PROJECT%\"

echo.
echo ✅ Fresh project created at: %NEW_PROJECT%
echo.
echo Next steps:
echo 1. Open %NEW_PROJECT% in your IDE
echo 2. Create virtual environment: python -m venv .venv
echo 3. Install dependencies: .venv\Scripts\pip install -r requirements.txt
echo 4. Run: .venv\Scripts\python.exe main.py
echo.
pause

