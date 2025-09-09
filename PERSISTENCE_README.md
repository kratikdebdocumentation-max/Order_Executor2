# Trade Persistence System

## Overview
The Order Executor trading bot now includes a comprehensive trade persistence system that ensures your active trades survive program restarts, disconnections, and system crashes.

## Features

### 🔄 Automatic Trade Recovery
- **Persistent Storage**: All active trades are automatically saved to `active_trades.json`
- **Startup Recovery**: Trades are automatically restored when the bot restarts
- **Context Restoration**: Telegram context is restored when you interact with the bot
- **Validation**: Only valid trades are restored (filters out old/invalid trades)

### 💾 Data Persistence
- **JSON Storage**: Trades are stored in a human-readable JSON format
- **Automatic Saving**: Trades are saved whenever they are created, modified, or deleted
- **Safe Serialization**: Non-serializable data (like Telegram context) is handled safely

### 🧹 Cleanup & Maintenance
- **Automatic Cleanup**: Old trades (>1 day) are automatically filtered out
- **Manual Cleanup**: Use `/cleanup` command to remove persisted trade files
- **Test Trade Filtering**: Test trades are not persisted to avoid clutter

## How It Works

### 1. Trade Creation
When you place a new trade:
```python
# Trade is automatically saved to active_trades.json
self.active_trades[order_id] = trade_data
self.save_active_trades()  # Automatic save
```

### 2. Program Restart
When the bot starts:
```python
# Loads persisted trades on startup
self.load_persisted_trades()

# Validates each trade
if self._validate_persisted_trade(trade_data):
    self.active_trades[order_id] = trade_data
```

### 3. Context Restoration
When you interact with the bot:
```python
# Restores Telegram context for recovered trades
self._restore_trade_contexts(update, context)
```

## File Structure

### `active_trades.json`
```json
{
  "ORDER_123": {
    "symbol": "RELIANCE-EQ",
    "sl": 2450.0,
    "tgt": 2550.0,
    "exch": "NSE",
    "token": "2881",
    "qty": 10,
    "entry_price": 2500.0,
    "entry_time": "2024-01-15 10:30:00",
    "order_status": "COMPLETE",
    "order_type": "MKT"
  }
}
```

## Commands

### `/cleanup`
- Removes the persisted trades file
- Active trades continue to be monitored
- Use when you want to start fresh

### `/trades`
- Shows all active trades including recovered ones
- Displays current PnL for each trade

## Recovery Process

### 1. Startup Recovery
```
🔄 Loading 2 persisted trades...
✅ Restored trade: RELIANCE-EQ (Order: ORDER_123)
✅ Restored trade: TCS-EQ (Order: ORDER_456)
✅ Successfully restored 2 valid trades
```

### 2. Context Restoration
When you send `/start` or any command:
```
🔄 Restoring context for 2 recovered trades
🔄 Trade Recovery Complete!

✅ Restored context for 2 active trades
📊 These trades are now being monitored for SL/Target
💡 Use /trades to view current status
```

## Validation Rules

### Trade Validation
- ✅ Required fields present (symbol, sl, tgt, etc.)
- ✅ Entry time is valid and not too old (< 1 day)
- ✅ Not a test trade
- ❌ Missing required fields
- ❌ Trade older than 1 day
- ❌ Test trades (marked with `is_test_trade: true`)

## Benefits

### 🛡️ Crash Protection
- Your trades survive unexpected crashes
- No manual intervention required
- Automatic recovery on restart

### 🔄 Seamless Restart
- Continue monitoring where you left off
- All SL/Target levels preserved
- Real-time monitoring resumes immediately

### 📊 Data Integrity
- Only valid trades are restored
- Automatic cleanup of old data
- Safe handling of serialization

## Testing

Run the test script to see persistence in action:
```bash
python test_persistence.py
```

## Troubleshooting

### Issue: Trades not restoring
- Check if `active_trades.json` exists
- Verify trade data is valid
- Check console logs for validation errors

### Issue: Context not restored
- Send any command to the bot (e.g., `/start`)
- Context is restored on first interaction
- Use `/trades` to verify trades are active

### Issue: Old trades persisting
- Use `/cleanup` to remove persisted file
- Trades older than 1 day are automatically filtered
- Test trades are not persisted

## Technical Details

### Persistence Methods
- `save_active_trades()`: Saves current trades to JSON
- `load_persisted_trades()`: Loads trades on startup
- `_validate_persisted_trade()`: Validates trade data
- `update_trade_context()`: Restores Telegram context

### File Management
- Automatic saving on trade changes
- Safe JSON serialization
- Error handling for file operations
- Cleanup utilities

This persistence system ensures your trading bot is robust and reliable, even in the face of unexpected interruptions.
