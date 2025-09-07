#!/bin/bash

# Docker Build Script for Order Executor Trading Bot
# This script builds and runs the trading bot in a Docker container

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Building Order Executor Trading Bot Docker Image${NC}"

# Check if config.json exists
if [ ! -f "config.json" ]; then
    echo -e "${RED}❌ Error: config.json not found!${NC}"
    echo -e "${YELLOW}💡 Please create config.json with your trading credentials first.${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}📦 Building Docker image...${NC}"
docker build -t order-executor-bot:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
else
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
fi

# Show image info
echo -e "${BLUE}📋 Image Information:${NC}"
docker images order-executor-bot:latest

echo -e "${GREEN}🎉 Build complete! You can now run the bot with:${NC}"
echo -e "${YELLOW}   docker run -d --name trading-bot -v \$(pwd)/config.json:/app/config.json -v \$(pwd)/trade_log.csv:/app/trade_log.csv order-executor-bot:latest${NC}"
echo -e "${YELLOW}   or use: docker-compose up -d${NC}"
