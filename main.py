"""
Main entry point for the Order Executor trading bot.
This modular version uses separate modules for different functionalities.
"""

import os
import sys
import psutil
from config import Config
from api_client import APIClient
from trade_logger import TradeLogger
from trading_engine import TradingEngine
from websocket_handler import WebSocketHandler
from telegram_bot import TelegramBot


def check_existing_instances():
    """Check if another instance of the bot is already running."""
    current_pid = os.getpid()
    current_script_path = os.path.abspath(__file__)
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1:
                    cmdline_str = ' '.join(cmdline)
                    # Check if this is another instance of our bot by looking for the exact main.py path
                    if (proc.info['pid'] != current_pid and 
                        current_script_path in cmdline_str and
                        'Order_Executor2' in cmdline_str):
                        print(f"🔍 Found existing bot instance: PID {proc.info['pid']}")
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def main():
    """Main function to initialize and start the trading bot."""
    print("🚀 Starting Order Executor Trading Bot...")
    
    # Check for existing instances
    if check_existing_instances():
        print("❌ Another instance of the bot is already running!")
        print("💡 Please stop the existing instance before starting a new one.")
        print("💡 You can use 'taskkill /f /im python.exe' to stop all Python processes.")
        return
    
    try:
        # Initialize configuration
        print("📋 Loading configuration...")
        config = Config()
        
        # Initialize API client
        print("🔌 Initializing API client...")
        api_client = APIClient(config)
        
        # Login to Shoonya
        print("🔐 Logging into Shoonya...")
        success, client_name = api_client.login()
        if not success:
            print("❌ Failed to login to Shoonya API")
            return
        
        # Initialize trade logger
        print("📊 Initializing trade logger...")
        trade_logger = TradeLogger(config.LOG_FILE)
        
        # Initialize trading engine
        print("⚙️ Initializing trading engine...")
        trading_engine = TradingEngine(config, api_client, trade_logger)
        
        # Initialize websocket handler
        print("🌐 Initializing websocket handler...")
        websocket_handler = WebSocketHandler(trading_engine)
        
        # Start websocket feed
        print("📡 Starting websocket feed...")
        if not websocket_handler.start_websocket(api_client):
            print("❌ Failed to start websocket feed")
            return
        
        # Resubscribe to active trades for real-time monitoring
        print("🔄 Resubscribing to active trades...")
        subscribed_count, failed_count = trading_engine.resubscribe_to_active_trades()
        if subscribed_count > 0:
            print(f"✅ Resubscribed to {subscribed_count} active trades for real-time monitoring")
        if failed_count > 0:
            print(f"⚠️ Failed to resubscribe to {failed_count} trades")
        
        # Initialize and start telegram bot
        print("🤖 Initializing Telegram bot...")
        telegram_bot = TelegramBot(config, api_client, trading_engine)
        
        # Handle trade recovery and context restoration
        print("🔄 Checking for recovered trades...")
        trades_needing_context = trading_engine.get_trades_needing_context()
        if trades_needing_context:
            print(f"📋 Found {len(trades_needing_context)} trades that need context restoration")
            print("💡 These trades will be monitored but won't send notifications until context is restored")
        else:
            print("✅ No trades need context restoration")
        
        # Show websocket resubscription status
        active_trades_count = len(trading_engine.active_trades)
        if active_trades_count > 0:
            print(f"📡 {active_trades_count} active trades are being monitored via websocket")
        
        print("✅ All systems initialized successfully!")
        print(f"👤 Logged in as: {client_name}")
        print("🎯 Bot is ready to accept trades!")
        print("=" * 50)
        
        # Start the telegram bot (this will block and handle startup notification)
        telegram_bot.start_bot()
        
    except FileNotFoundError as e:
        print(f"❌ Configuration error: {e}")
        print("💡 Make sure 'credentials.json' exists with proper credentials")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Check your configuration and try again")


if __name__ == "__main__":
    main()