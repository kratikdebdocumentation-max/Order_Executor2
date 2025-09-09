#!/usr/bin/env python3
"""
Simple test script to verify Telegram bot connectivity
"""

import requests
import json

# Bot token from config
BOT_TOKEN = "8446199814:AAF6wnkw0zVkLVYPLvBtUvQtmMV_QTFM2GM"
CHAT_ID = "-1003012708677"

def test_bot_connection():
    """Test if the bot token is valid"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                print("✅ Bot token is valid!")
                print(f"Bot info: {data['result']}")
                return True
            else:
                print(f"❌ Bot API error: {data}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_send_message():
    """Test sending a message to the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': '🤖 Bot test message - Bot is working!'
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"Response: {result}")
        
        if response.status_code == 200:
            if result.get('ok'):
                print("✅ Test message sent successfully!")
                return True
            else:
                print(f"❌ Failed to send message: {result}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Error details: {result}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def get_chat_info():
    """Get information about the chat"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
    data = {'chat_id': CHAT_ID}
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        print(f"Chat info: {result}")
        return result.get('ok', False)
    except Exception as e:
        print(f"❌ Error getting chat info: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Telegram Bot Connection...")
    print("=" * 50)
    
    # Test bot connection
    if test_bot_connection():
        print("\n📋 Getting chat information...")
        get_chat_info()
        
        print("\n📤 Testing message sending...")
        test_send_message()
    
    print("\n" + "=" * 50)
    print("Test completed!")
