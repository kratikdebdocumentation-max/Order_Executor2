@echo off
REM Docker Build Script for Order Executor Trading Bot (Windows)
REM This script builds and runs the trading bot in a Docker container

echo 🐳 Building Order Executor Trading Bot Docker Image

REM Check if config.json exists
if not exist "config.json" (
    echo ❌ Error: config.json not found!
    echo 💡 Please create config.json with your trading credentials first.
    pause
    exit /b 1
)

REM Build the Docker image
echo 📦 Building Docker image...
docker build -t order-executor-bot:latest .

if %errorlevel% equ 0 (
    echo ✅ Docker image built successfully!
) else (
    echo ❌ Docker build failed!
    pause
    exit /b 1
)

REM Show image info
echo 📋 Image Information:
docker images order-executor-bot:latest

echo 🎉 Build complete! You can now run the bot with:
echo    docker run -d --name trading-bot -v %cd%/config.json:/app/config.json -v %cd%/trade_log.csv:/app/trade_log.csv order-executor-bot:latest
echo    or use: docker-compose up -d

pause
