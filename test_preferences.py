#!/usr/bin/env python3
"""
Test script to demonstrate user preferences functionality.
This script shows how user preferences are saved and loaded.
"""

import json
import os
from datetime import datetime

def test_user_preferences():
    """Test the user preferences functionality."""
    print("🧪 Testing User Preferences System")
    print("=" * 50)
    
    # Create sample preferences
    preferences = {
        "capital": 50000,
        "sl_percent": 0.5,
        "target_percent": 1.0,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Save preferences to file
    preferences_file = "user_preferences.json"
    print(f"💾 Saving user preferences to {preferences_file}")
    
    with open(preferences_file, 'w') as f:
        json.dump(preferences, f, indent=2)
    
    print("✅ Preferences saved successfully!")
    print(f"   💰 Capital: ₹{preferences['capital']:,}")
    print(f"   📉 SL: {preferences['sl_percent']}%")
    print(f"   🎯 Target: {preferences['target_percent']}%")
    print(f"   ⏰ Last Updated: {preferences['last_updated']}")
    
    # Simulate program restart - load preferences
    print("\n🔄 Simulating program restart...")
    print("📁 Loading user preferences...")
    
    if os.path.exists(preferences_file):
        with open(preferences_file, 'r') as f:
            loaded_preferences = json.load(f)
        
        print("✅ Preferences loaded successfully!")
        print(f"   💰 Capital: ₹{loaded_preferences['capital']:,}")
        print(f"   📉 SL: {loaded_preferences['sl_percent']}%")
        print(f"   🎯 Target: {loaded_preferences['target_percent']}%")
        print(f"   ⏰ Last Updated: {loaded_preferences['last_updated']}")
        
        # Check if preferences are complete
        has_complete = all([
            loaded_preferences.get("capital") is not None,
            loaded_preferences.get("sl_percent") is not None,
            loaded_preferences.get("target_percent") is not None
        ])
        
        print(f"\n📊 Complete preferences: {'✅ Yes' if has_complete else '❌ No'}")
        
        if has_complete:
            print("\n🎯 Welcome back! Your current settings:")
            print(f"💰 Capital: ₹{loaded_preferences['capital']:,}")
            print(f"📉 SL: {loaded_preferences['sl_percent']}%")
            print(f"🎯 Target: {loaded_preferences['target_percent']}%")
            print("\n✅ Ready to trade with these settings!")
    else:
        print("❌ No preferences file found")
    
    # Clean up
    print(f"\n🧹 Cleaning up test file...")
    if os.path.exists(preferences_file):
        os.remove(preferences_file)
        print("✅ Test file cleaned up")

if __name__ == "__main__":
    test_user_preferences()
