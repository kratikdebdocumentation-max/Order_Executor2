# 🐳 Docker Deployment Guide

This guide explains how to deploy the Order Executor Trading Bot using Docker.

## 📋 Prerequisites

- Docker installed on your system
- Docker Compose (optional, for easier management)
- `config.json` file with your trading credentials

## 🚀 Quick Start

### Method 1: Using Docker Compose (Recommended)

1. **Prepare your configuration:**
   ```bash
   # Ensure config.json exists with your credentials
   cp config.json.example config.json
   # Edit config.json with your actual trading credentials
   ```

2. **Build and run:**
   ```bash
   docker-compose up -d
   ```

3. **Check logs:**
   ```bash
   docker-compose logs -f trading-bot
   ```

### Method 2: Using Docker Commands

1. **Build the image:**
   ```bash
   # On Linux/Mac
   chmod +x build-docker.sh
   ./build-docker.sh
   
   # On Windows
   build-docker.bat
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name trading-bot \
     -v $(pwd)/config.json:/app/config.json:ro \
     -v $(pwd)/trade_log.csv:/app/trade_log.csv \
     -v $(pwd)/logs:/app/logs \
     order-executor-bot:latest
   ```

## 🔧 Configuration

### Environment Variables

You can override settings using environment variables:

```bash
docker run -d \
  --name trading-bot \
  -e TZ=Asia/Kolkata \
  -e DEBUG=false \
  -v $(pwd)/config.json:/app/config.json:ro \
  order-executor-bot:latest
```

### Volume Mounts

- `config.json` - Trading credentials (read-only)
- `trade_log.csv` - Trade history (read-write)
- `logs/` - Application logs (read-write)

## 📊 Monitoring

### View Logs
```bash
# Real-time logs
docker logs -f trading-bot

# Last 100 lines
docker logs --tail 100 trading-bot
```

### Check Status
```bash
# Container status
docker ps

# Resource usage
docker stats trading-bot
```

### Access Container
```bash
# Execute commands inside container
docker exec -it trading-bot bash

# View files
docker exec -it trading-bot ls -la /app
```

## 🔄 Management Commands

### Start/Stop/Restart
```bash
# Start
docker start trading-bot

# Stop
docker stop trading-bot

# Restart
docker restart trading-bot
```

### Update Bot
```bash
# Stop current container
docker stop trading-bot
docker rm trading-bot

# Rebuild image
docker build -t order-executor-bot:latest .

# Run new container
docker run -d --name trading-bot \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/trade_log.csv:/app/trade_log.csv \
  order-executor-bot:latest
```

## 🛠️ Troubleshooting

### Common Issues

1. **Config file not found:**
   ```bash
   # Ensure config.json exists and is readable
   ls -la config.json
   ```

2. **Permission denied:**
   ```bash
   # Fix file permissions
   chmod 644 config.json
   chmod 666 trade_log.csv
   ```

3. **Container won't start:**
   ```bash
   # Check logs for errors
   docker logs trading-bot
   ```

4. **Port conflicts:**
   ```bash
   # Check if port is in use
   netstat -tulpn | grep :8080
   ```

### Health Checks

The container includes health checks:
```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' trading-bot
```

## 🔒 Security Considerations

1. **File Permissions:** Ensure config.json has proper permissions (600)
2. **Volume Mounts:** Use read-only mounts for sensitive files
3. **User Context:** Container runs as non-root user
4. **Network:** No exposed ports by default

## 📈 Performance

### Resource Limits

Default limits (adjustable in docker-compose.yml):
- Memory: 512MB limit, 256MB reservation
- CPU: 0.5 cores limit, 0.25 cores reservation

### Optimization Tips

1. **Use .dockerignore** to exclude unnecessary files
2. **Multi-stage builds** for smaller images
3. **Volume optimization** for persistent data
4. **Resource monitoring** for performance tuning

## 🚀 Production Deployment

### Using Docker Compose

1. **Create production override:**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     trading-bot:
       restart: always
       deploy:
         resources:
           limits:
             memory: 1G
             cpus: '1.0'
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml trading-bot
```

## 📝 Maintenance

### Regular Tasks

1. **Update dependencies:**
   ```bash
   docker build --no-cache -t order-executor-bot:latest .
   ```

2. **Clean up:**
   ```bash
   # Remove unused images
   docker image prune
   
   # Remove unused containers
   docker container prune
   ```

3. **Backup data:**
   ```bash
   # Backup trade log
   cp trade_log.csv backup/trade_log_$(date +%Y%m%d).csv
   ```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker logs trading-bot`
2. Verify configuration: `docker exec -it trading-bot cat /app/config.json`
3. Test connectivity: `docker exec -it trading-bot python -c "import requests; print('OK')"`
4. Check resource usage: `docker stats trading-bot`

---

**Happy Trading! 🚀📈**
