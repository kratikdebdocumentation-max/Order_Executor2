#!/usr/bin/env python3
"""
Demo script showing the startup notification that gets sent to Telegram.
This demonstrates what users will receive when the bot starts.
"""

from datetime import datetime

def demo_startup_notification():
    """Demonstrate the startup notification message."""
    print("📱 TELEGRAM STARTUP NOTIFICATION DEMO")
    print("=" * 60)
    
    # Simulate current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Simulate user preferences
    preferences = {
        "capital": 100000,
        "sl_percent": 0.5,
        "target_percent": 1.0,
        "last_updated": "2024-01-15 09:15:00"
    }
    
    # Simulate active trades
    active_trades = [
        {
            "symbol": "RELIANCE-EQ",
            "entry_price": 2450.0,
            "current_price": 2475.0,
            "sl": 2440.0,
            "tgt": 2490.0,
            "current_pnl": 250.0,
            "current_pnl_pct": 1.02,
            "order_status": "COMPLETE",
            "qty": 20
        },
        {
            "symbol": "TCS-EQ", 
            "entry_price": 3850.0,
            "current_price": 3820.0,
            "sl": 3840.0,
            "tgt": 3880.0,
            "current_pnl": -300.0,
            "current_pnl_pct": -0.78,
            "order_status": "COMPLETE",
            "qty": 10
        },
        {
            "symbol": "INFY-EQ",
            "entry_price": 1650.0,
            "current_price": 1650.0,
            "sl": 1640.0,
            "tgt": 1670.0,
            "current_pnl": 0.0,
            "current_pnl_pct": 0.0,
            "order_status": "PENDING",
            "qty": 30
        }
    ]
    
    # Build the startup notification message
    print("\n📱 TELEGRAM MESSAGE:")
    print("=" * 60)
    
    # Bot status
    print("🚀 **Order Executor Bot Started Successfully!**")
    print(f"⏰ **Time:** {current_time}")
    print("=" * 50)
    print()
    
    # User preferences
    print("📊 **Your Trading Settings:**")
    print(f"💰 Capital: ₹{preferences['capital']:,}")
    print(f"📉 SL: {preferences['sl_percent']}%")
    print(f"🎯 Target: {preferences['target_percent']}%")
    print(f"⏰ Last Updated: {preferences['last_updated']}")
    print()
    
    # Trade recovery status
    trades_needing_context = 2  # Simulate some trades needing context
    print(f"🔄 **Trade Recovery:** {trades_needing_context} trades restored")
    print("💡 Context will be restored when you interact with the bot")
    print()
    
    # Active trades
    print("📊 **Active Trades:**")
    
    total_pnl = 0
    valid_trades = 0
    pending_trades = 0
    completed_trades = 0
    
    for trade in active_trades:
        order_status = trade['order_status']
        
        # Count by status
        if order_status == 'PENDING':
            pending_trades += 1
        elif order_status == 'COMPLETE':
            completed_trades += 1
        
        # Calculate PnL
        if trade["current_pnl"] != "N/A":
            total_pnl += trade["current_pnl"]
            valid_trades += 1
            
            # Format PnL with color emoji
            pnl_emoji = "📈" if trade["current_pnl"] >= 0 else "📉"
            pnl_color = "🟢" if trade["current_pnl"] >= 0 else "🔴"
            
            status_emoji = "⏳" if order_status == 'PENDING' else "✅" if order_status == 'COMPLETE' else "❓"
            
            print(f"{status_emoji} **{trade['symbol']}** {pnl_color}")
            print(f"   💰 Entry: ₹{trade['entry_price']} → Current: ₹{trade['current_price']}")
            print(f"   {pnl_emoji} PnL: ₹{trade['current_pnl']} ({trade['current_pnl_pct']}%)")
            print(f"   📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}")
            print()
    
    # Summary statistics
    if valid_trades > 0:
        avg_pnl = total_pnl / valid_trades
        print(f"📊 **Summary:** Total PnL: ₹{total_pnl:.2f} | Avg: ₹{avg_pnl:.2f}")
    
    print(f"🔢 **Count:** {len(active_trades)} total", end="")
    if pending_trades > 0:
        print(f" | {pending_trades} pending", end="")
    if completed_trades > 0:
        print(f" | {completed_trades} filled", end="")
    print()
    print()
    
    # Websocket status
    monitorable_trades = len(active_trades)
    print(f"📡 **Monitoring:** {monitorable_trades} trades via websocket ✅")
    print()
    
    # System status
    print("🔧 **System Status:**")
    print("✅ API Connection: Active")
    print("✅ WebSocket: Connected")
    print("✅ Trade Monitoring: Enabled")
    print("✅ Notifications: Enabled")
    print()
    
    # Quick actions
    print("🎯 **Quick Actions:**")
    print("• Send any symbol to start trading")
    print("• Use /trades to view detailed PnL")
    print("• Use /m to modify existing trades")
    print("• Use /help for all commands")
    print()
    
    # Footer
    print("🤖 **Bot is ready to accept trades!**")
    
    print("\n" + "=" * 60)
    print("🎯 This notification is automatically sent to your Telegram chat")
    print("📱 when the bot starts, giving you complete visibility into your trading status")
    print("🔄 All active trades are automatically resubscribed to websocket")
    print("⚡ Real-time monitoring resumes immediately")

if __name__ == "__main__":
    demo_startup_notification()
