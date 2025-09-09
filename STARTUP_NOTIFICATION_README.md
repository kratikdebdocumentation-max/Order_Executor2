# Startup Notification System

## Overview
The Order Executor trading bot now sends a comprehensive startup notification to your Telegram chat whenever the bot starts. This gives you complete visibility into your trading status, active trades, and system health right when the bot comes online.

## Features

### 📱 Automatic Telegram Notification
- **Startup Message**: Sent automatically when bot starts
- **Complete Overview**: Shows all trading parameters and active trades
- **Real-time Status**: Displays current PnL and trade status
- **System Health**: Shows connection and monitoring status

### 📊 Comprehensive Information Display
- **Trading Settings**: Your saved capital, SL%, and target%
- **Active Trades**: All current positions with real-time PnL
- **Trade Recovery**: Shows how many trades were restored
- **Websocket Status**: Monitoring status for all trades
- **System Status**: API, websocket, and notification status

### 🎯 Quick Actions Guide
- **Trading Commands**: How to start new trades
- **Management Commands**: How to modify existing trades
- **Help Commands**: Quick reference for all functions

## Notification Content

### 🚀 Bot Status
```
🚀 Order Executor Bot Started Successfully!
⏰ Time: 2024-01-15 14:30:00
==================================================
```

### 📊 Trading Settings
```
📊 Your Trading Settings:
💰 Capital: ₹100,000
📉 SL: 0.5%
🎯 Target: 1.0%
⏰ Last Updated: 2024-01-15 09:15:00
```

### 🔄 Trade Recovery
```
🔄 Trade Recovery: 2 trades restored
💡 Context will be restored when you interact with the bot
```

### 📊 Active Trades
```
📊 Active Trades:
✅ RELIANCE-EQ 🟢
   💰 Entry: ₹2450.0 → Current: ₹2475.0
   📈 PnL: ₹250.0 (1.02%)
   📉 SL: ₹2440.0 | 🎯 Target: ₹2490.0

✅ TCS-EQ 🔴
   💰 Entry: ₹3850.0 → Current: ₹3820.0
   📉 PnL: ₹-300.0 (-0.78%)
   📉 SL: ₹3840.0 | 🎯 Target: ₹3880.0

⏳ INFY-EQ ⚪
   💰 Entry: ₹1650.0 → Current: ₹1650.0
   📉 SL: ₹1640.0 | 🎯 Target: ₹1670.0

📊 Summary: Total PnL: ₹-50.00 | Avg: ₹-25.00
🔢 Count: 3 total | 1 pending | 2 filled
```

### 📡 Monitoring Status
```
📡 Monitoring: 3 trades via websocket ✅
```

### 🔧 System Status
```
🔧 System Status:
✅ API Connection: Active
✅ WebSocket: Connected
✅ Trade Monitoring: Enabled
✅ Notifications: Enabled
```

### 🎯 Quick Actions
```
🎯 Quick Actions:
• Send any symbol to start trading
• Use /trades to view detailed PnL
• Use /m to modify existing trades
• Use /help for all commands
```

## Technical Implementation

### Automatic Sending
- **Timing**: Sent after all systems are initialized
- **Error Handling**: Graceful fallback if notification fails
- **Async Processing**: Non-blocking notification sending

### Message Building
- **Dynamic Content**: Real-time data from active trades
- **Status Indicators**: Visual emojis for quick understanding
- **Comprehensive Coverage**: All important information included

### Error Handling
- **Connection Issues**: Handles Telegram API errors
- **Missing Data**: Graceful handling of incomplete information
- **Fallback Messages**: Basic notification if detailed message fails

## Benefits

### 🎯 Complete Visibility
- **Instant Overview**: See everything at a glance
- **Real-time Data**: Current prices and PnL
- **Status Awareness**: Know what's being monitored

### 🚀 Quick Start
- **No Manual Checking**: Everything is shown automatically
- **Immediate Action**: Know exactly what to do next
- **Context Restoration**: Understand trade recovery status

### 📱 Mobile Friendly
- **Telegram Optimized**: Perfect for mobile viewing
- **Rich Formatting**: Markdown formatting for clarity
- **Emoji Indicators**: Visual status indicators

## Configuration

### Required Settings
- **Telegram Chat ID**: Must be configured in config.json
- **Bot Token**: Valid Telegram bot token required
- **API Connection**: Shoonya API must be connected

### Optional Features
- **Trade Recovery**: Works with or without active trades
- **Preferences**: Shows saved settings if available
- **Websocket**: Displays monitoring status

## Troubleshooting

### Issue: No notification received
- Check Telegram chat ID in config.json
- Verify bot token is correct
- Check console logs for error messages

### Issue: Incomplete information
- Ensure all systems are properly initialized
- Check API connection status
- Verify trade data is valid

### Issue: Notification errors
- Check internet connection
- Verify Telegram bot permissions
- Review error logs for details

## File Structure

### Modified Files
- **`telegram_bot.py`**: Added notification methods
- **`main.py`**: Added notification sending on startup

### New Methods
- **`send_startup_notification()`**: Main notification method
- **`_build_startup_message()`**: Message construction
- **`_send_startup_notification_async()`**: Async sending

## Usage

### Automatic
The notification is sent automatically when you start the bot:
```bash
python main.py
```

### Manual Testing
You can test the notification format using:
```bash
python demo_startup_notification.py
```

## Example Scenarios

### Fresh Start (No Active Trades)
- Shows trading settings
- Indicates no active trades
- Provides quick action guide

### With Active Trades
- Shows all active trades with PnL
- Displays monitoring status
- Indicates trade recovery status

### With Trade Recovery
- Shows recovered trades
- Indicates context restoration needed
- Provides guidance for interaction

This startup notification system ensures you always have complete visibility into your trading bot's status and your active positions, making it easy to understand what's happening and what actions you can take.
