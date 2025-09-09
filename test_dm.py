#!/usr/bin/env python3
"""
Test script to send a direct message to the bot
"""

import requests
import json

# Bot token from config
BOT_TOKEN = "8446199814:AAF6wnkw0zVkLVYPLvBtUvQtmMV_QTFM2GM"

def get_updates():
    """Get recent updates from the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        print("Recent updates:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"❌ Error getting updates: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Getting recent bot updates...")
    print("=" * 50)
    get_updates()
