#!/usr/bin/env python3
"""
Demo script showing the enhanced welcome message with active trades and websocket status.
This demonstrates what users will see when they restart the bot with active trades.
"""

def demo_welcome_message():
    """Demonstrate the enhanced welcome message."""
    print("🎯 Enhanced Welcome Message Demo")
    print("=" * 60)
    
    # Simulate user preferences
    preferences = {
        "capital": 75000,
        "sl_percent": 0.4,
        "target_percent": 0.8,
        "last_updated": "2024-01-15 14:30:00"
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
            "qty": 10
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
            "qty": 5
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
            "qty": 20
        }
    ]
    
    # Build welcome message
    print("\n📱 TELEGRAM BOT WELCOME MESSAGE:")
    print("=" * 60)
    
    # User settings
    print("👋 **Welcome back!**")
    print()
    print("📊 **Your Current Settings:**")
    print(f"💰 Capital: ₹{preferences['capital']:,}")
    print(f"📉 SL: {preferences['sl_percent']}%")
    print(f"🎯 Target: {preferences['target_percent']}%")
    print(f"⏰ Last Updated: {preferences['last_updated']}")
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
    monitorable_trades = len(active_trades)  # All trades have exchange/token data
    print(f"📡 **Monitoring:** {monitorable_trades} trades via websocket ✅")
    print()
    
    # Action prompt
    print("🎯 Ready to trade with these settings?")
    print()
    
    # Inline buttons (simulated)
    print("📱 INLINE BUTTONS:")
    print("┌─────────────────────────────────────────────────┐")
    print("│  [✅ Continue Trading]  [⚙️ Modify Settings]   │")
    print("│  [📊 View Active Trades] [🔍 Search Symbol]    │")
    print("└─────────────────────────────────────────────────┘")
    
    print("\n" + "=" * 60)
    print("🎯 This is what users will see when they restart the bot!")
    print("✅ All active trades are automatically resubscribed to websocket")
    print("📊 Real-time monitoring resumes immediately")
    print("🔄 Context is restored when user interacts with the bot")

if __name__ == "__main__":
    demo_welcome_message()
