#!/usr/bin/env python3
"""
Test script to demonstrate trade persistence functionality.
This script shows how trades are saved and restored.
"""

import json
import os
from datetime import datetime

def create_sample_trade():
    """Create a sample trade for testing."""
    return {
        "symbol": "RELIANCE-EQ",
        "sl": 2450.0,
        "tgt": 2550.0,
        "sl_percent": 0.5,
        "target_percent": 1.0,
        "exch": "NSE",
        "token": "2881",
        "qty": 10,
        "entry_price": 2500.0,
        "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order_status": "COMPLETE",
        "order_type": "MKT",
        "limit_price": None
    }

def test_persistence():
    """Test the persistence functionality."""
    print("🧪 Testing Trade Persistence System")
    print("=" * 50)
    
    # Create sample trades
    sample_trades = {
        "ORDER_123": create_sample_trade(),
        "ORDER_456": create_sample_trade()
    }
    
    # Save trades to file
    persistence_file = "active_trades.json"
    print(f"💾 Saving {len(sample_trades)} trades to {persistence_file}")
    
    with open(persistence_file, 'w') as f:
        json.dump(sample_trades, f, indent=2)
    
    print("✅ Trades saved successfully!")
    
    # Simulate program restart - load trades
    print("\n🔄 Simulating program restart...")
    print("📁 Loading persisted trades...")
    
    if os.path.exists(persistence_file):
        with open(persistence_file, 'r') as f:
            loaded_trades = json.load(f)
        
        print(f"✅ Loaded {len(loaded_trades)} trades:")
        for order_id, trade in loaded_trades.items():
            print(f"   📌 {trade['symbol']} - Entry: ₹{trade['entry_price']} - SL: ₹{trade['sl']} - Target: ₹{trade['tgt']}")
    else:
        print("❌ No persisted trades found")
    
    # Clean up
    print(f"\n🧹 Cleaning up test file...")
    if os.path.exists(persistence_file):
        os.remove(persistence_file)
        print("✅ Test file cleaned up")

if __name__ == "__main__":
    test_persistence()
