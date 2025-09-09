# User Preferences System

## Overview
The Order Executor trading bot now remembers your trading parameters (capital, stoploss, target) and provides a convenient interface to continue trading with saved settings or modify them as needed.

## Features

### 💾 Automatic Preference Saving
- **Capital**: Your trading amount is saved when entered
- **Stoploss %**: Your SL percentage is saved when set
- **Target %**: Your target percentage is saved when set
- **Last Updated**: Timestamp of when preferences were last modified

### 🎯 Smart Startup Experience
- **Welcome Back**: Shows your saved settings on startup
- **Inline Buttons**: Quick access to common actions
- **One-Click Trading**: Continue with saved settings instantly
- **Easy Modification**: Update settings with a single click

### 🔄 Seamless Integration
- **Context Loading**: Saved preferences are loaded into trading context
- **State Management**: Bot remembers where you left off
- **Error Handling**: Graceful fallback if preferences are corrupted

## How It Works

### 1. First Time Setup
When you start the bot for the first time:
```
👋 Welcome! How much capital do you want to trade with?
💰 Enter amount: 50000
📉 Enter Stoploss %: 0.5
🎯 Enter Target %: 1.0
✅ Setup complete! Now send me a stock name or symbol.
```

### 2. Subsequent Starts
When you restart the bot with saved preferences:
```
👋 Welcome back!

📊 Your Current Settings:
💰 Capital: ₹50,000
📉 SL: 0.5%
🎯 Target: 1.0%
⏰ Last Updated: 2024-01-15 10:30:00

🎯 Ready to trade with these settings?

[✅ Continue Trading] [⚙️ Modify Settings]
[📊 View Active Trades] [🔍 Search Symbol]
```

### 3. Inline Button Actions

#### ✅ Continue Trading
- Loads your saved preferences
- Sets up trading context
- Ready to accept symbol input immediately

#### ⚙️ Modify Settings
- Starts the setup process again
- Allows you to update any parameter
- Saves new preferences automatically

#### 📊 View Active Trades
- Shows all active trades with current PnL
- Displays real-time profit/loss
- No need to use separate commands

#### 🔍 Search Symbol
- Quick access to symbol search
- Ready for immediate trading
- Uses your saved settings

## File Structure

### `user_preferences.json`
```json
{
  "capital": 50000,
  "sl_percent": 0.5,
  "target_percent": 1.0,
  "last_updated": "2024-01-15 10:30:00"
}
```

## User Experience Flow

### New User (First Time)
1. Send `/start`
2. Enter capital amount
3. Enter stoploss percentage
4. Enter target percentage
5. Start trading with symbol input

### Returning User (With Saved Preferences)
1. Send `/start`
2. See welcome message with saved settings
3. Choose action via inline buttons:
   - **Continue Trading**: Use saved settings
   - **Modify Settings**: Update parameters
   - **View Trades**: Check active positions
   - **Search Symbol**: Quick symbol lookup

## Technical Implementation

### Preference Management
- **Auto-Save**: Preferences saved on each input
- **Validation**: Ensures data integrity
- **Fallback**: Graceful handling of missing data
- **Persistence**: Survives program restarts

### State Management
- **Context Loading**: Preferences loaded into user context
- **State Transitions**: Smooth flow between states
- **Error Recovery**: Handles invalid inputs gracefully

### UI/UX Features
- **Inline Keyboards**: Modern button interface
- **Rich Formatting**: Markdown formatting for better readability
- **Emoji Icons**: Visual indicators for different actions
- **Responsive Design**: Adapts to different message lengths

## Benefits

### 🚀 Faster Trading
- No need to re-enter parameters every time
- One-click access to common actions
- Streamlined trading workflow

### 🎯 Better UX
- Modern inline button interface
- Clear visual feedback
- Intuitive navigation

### 💾 Data Persistence
- Settings survive program restarts
- Automatic backup of preferences
- Easy to modify when needed

### 🔄 Seamless Integration
- Works with existing trade persistence
- Maintains all bot functionality
- Backward compatible

## Commands

### `/start`
- Shows welcome message with saved preferences
- Provides inline buttons for quick actions
- Loads preferences into trading context

### Other Commands
- All existing commands work as before
- Preferences are loaded automatically
- No changes to existing functionality

## Testing

Run the test script to see preferences in action:
```bash
python test_preferences.py
```

## Troubleshooting

### Issue: Preferences not saving
- Check file permissions for `user_preferences.json`
- Verify JSON format is valid
- Check console logs for errors

### Issue: Preferences not loading
- Ensure `user_preferences.json` exists
- Check file format and content
- Verify all required fields are present

### Issue: Inline buttons not working
- Ensure you're using a supported Telegram client
- Check if callback handlers are properly registered
- Verify button callback data matches handlers

## File Management

### Automatic Cleanup
- Preferences are saved automatically
- No manual intervention required
- Safe JSON serialization

### Backup
- Preferences file can be backed up manually
- Contains all user settings
- Easy to restore if needed

This user preferences system makes your trading bot much more user-friendly and efficient, providing a modern, intuitive interface that remembers your settings and allows for quick, seamless trading.
