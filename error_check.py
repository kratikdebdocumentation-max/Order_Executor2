#!/usr/bin/env python3
"""
Comprehensive error check script for the Order Executor trading bot.
This script checks for common issues and validates the configuration.
"""

import json
import os
import sys
from datetime import datetime

def check_config_file():
    """Check if config.json exists and has required fields."""
    print("🔍 Checking configuration file...")
    
    if not os.path.exists("config.json"):
        print("❌ config.json not found!")
        return False
    
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        required_fields = [
            "username", "pwd", "factor2", "vc", "app_key", "imei",
            "telegram_bot_token", "telegram_chat_id", "default_product_type"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        print("✅ Configuration file is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        return False

def check_python_files():
    """Check Python files for syntax errors."""
    print("\n🔍 Checking Python files for syntax errors...")
    
    python_files = [
        "main.py", "config.py", "telegram_bot.py", "trading_engine.py",
        "api_client.py", "trade_logger.py", "websocket_handler.py", "utils.py"
    ]
    
    all_good = True
    
    for filename in python_files:
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                # Try to compile the source
                compile(source, filename, 'exec')
                print(f"✅ {filename}: Syntax OK")
                
            except SyntaxError as e:
                print(f"❌ {filename}: Syntax Error")
                print(f"   Line {e.lineno}: {e.text}")
                print(f"   Error: {e.msg}")
                all_good = False
            except Exception as e:
                print(f"⚠️ {filename}: Error reading file - {e}")
                all_good = False
        else:
            print(f"⚠️ {filename}: File not found")
    
    return all_good

def check_imports():
    """Check if all required modules can be imported."""
    print("\n🔍 Checking module imports...")
    
    try:
        from config import Config
        print("✅ config module: OK")
    except Exception as e:
        print(f"❌ config module: {e}")
        return False
    
    try:
        from api_client import APIClient
        print("✅ api_client module: OK")
    except Exception as e:
        print(f"❌ api_client module: {e}")
        return False
    
    try:
        from trade_logger import TradeLogger
        print("✅ trade_logger module: OK")
    except Exception as e:
        print(f"❌ trade_logger module: {e}")
        return False
    
    try:
        from trading_engine import TradingEngine
        print("✅ trading_engine module: OK")
    except Exception as e:
        print(f"❌ trading_engine module: {e}")
        return False
    
    try:
        from websocket_handler import WebSocketHandler
        print("✅ websocket_handler module: OK")
    except Exception as e:
        print(f"❌ websocket_handler module: {e}")
        return False
    
    try:
        from telegram_bot import TelegramBot
        print("✅ telegram_bot module: OK")
    except Exception as e:
        print(f"❌ telegram_bot module: {e}")
        return False
    
    try:
        from utils import parse_percentage, calculate_pnl, format_pnl_message, is_market_open
        print("✅ utils module: OK")
    except Exception as e:
        print(f"❌ utils module: {e}")
        return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed."""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = [
        "requests", "websocket-client", "pandas", "yaml", "pyotp", 
        "retrying", "telegram", "pytz"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == "yaml":
                import yaml
            elif package == "telegram":
                import telegram
            else:
                __import__(package)
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_channel_config():
    """Check channel configuration."""
    print("\n🔍 Checking channel configuration...")
    
    try:
        with open("config.json", 'r') as f:
            config = json.load(f)
        
        channel_id = config.get("telegram_chat_id")
        bot_token = config.get("telegram_bot_token")
        
        if not channel_id:
            print("❌ No channel ID configured")
            return False
        
        if not bot_token:
            print("❌ No bot token configured")
            return False
        
        print(f"✅ Channel ID: {channel_id}")
        print(f"✅ Bot Token: {bot_token[:10]}...")
        
        # Check if channel ID looks valid
        if channel_id.startswith("-100"):
            print("✅ Channel ID format looks correct")
        else:
            print("⚠️ Channel ID format might be incorrect (should start with -100)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking channel config: {e}")
        return False

def main():
    """Run all error checks."""
    print("🚀 Order Executor Bot - Error Check")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Run all checks
    checks = [
        ("Configuration File", check_config_file),
        ("Python Files", check_python_files),
        ("Module Imports", check_imports),
        ("Dependencies", check_dependencies),
        ("Channel Configuration", check_channel_config)
    ]
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_checks_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 All checks passed! Your bot should work correctly.")
        print("\n📋 Next steps:")
        print("1. Add your bot to the Telegram channel as an administrator")
        print("2. Give the bot these permissions:")
        print("   - Post messages")
        print("   - Edit messages")
        print("   - Delete messages")
        print("3. Run: python main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above before running the bot.")
        print("\n💡 Common fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Check your config.json file")
        print("- Ensure all Python files are in the same directory")
    
    return all_checks_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
