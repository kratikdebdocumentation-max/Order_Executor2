"""
Telegram bot module for user interaction and conversation handling.
Handles all Telegram bot commands, conversations, and user interactions.
"""

import csv
from datetime import datetime
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes, CallbackQueryHandler
)
from api_client import APIClient
from trading_engine import TradingEngine
from config import Config
from utils import parse_percentage


class TelegramBot:
    """Handles Telegram bot interactions and conversations."""
    
    def __init__(self, config: Config, api_client: APIClient, trading_engine: TradingEngine):
        """Initialize telegram bot with dependencies."""
        self.config = config
        self.api_client = api_client
        self.trading_engine = trading_engine
        self.app = None
    
    async def start_command(self, update, context):
        """Handle /start command."""
        # Restore context for any recovered trades
        self._restore_trade_contexts(update, context)
        
        # Check if user has saved preferences
        if self.config.has_complete_preferences():
            # Show saved preferences with inline buttons
            preferences_summary = self.config.get_preferences_summary()
            
            # Get active trades information
            active_trades_info = self._get_active_trades_summary()
            
            # Get websocket status
            websocket_status = self._get_websocket_status()
            
            welcome_msg = (
                f"👋 **Welcome back!**\n\n"
                f"📊 **Your Current Settings:**\n{preferences_summary}\n\n"
                f"{active_trades_info}\n"
                f"{websocket_status}\n"
                f"🎯 Ready to trade with these settings?"
            )
            
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Continue Trading", callback_data="continue_trading"),
                    InlineKeyboardButton("⚙️ Modify Settings", callback_data="modify_settings")
                ],
                [
                    InlineKeyboardButton("📊 View Active Trades", callback_data="view_trades"),
                    InlineKeyboardButton("🔍 Search Symbol", callback_data="search_symbol")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
            return self.config.READY
        else:
            # No saved preferences, start fresh
            await update.message.reply_text("👋 Welcome! How much capital do you want to trade with?")
            return self.config.ASK_CAPITAL
    
    async def ask_sl_handler(self, update, context):
        """Handle capital input and ask for stoploss."""
        try:
            capital = float(update.message.text.strip())
            if capital <= 0:
                await update.message.reply_text("❌ Capital must be greater than 0. Enter a valid amount.")
                return self.config.ASK_CAPITAL
            context.user_data["capital"] = capital
            
            # Save capital to preferences
            self.config.save_user_preferences(capital=capital)
            
            await update.message.reply_text("📉 Enter Stoploss % (e.g., 0.2 or 0.2%)")
            return self.config.ASK_SL
        except ValueError:
            await update.message.reply_text("❌ Invalid capital. Enter a valid number (e.g., 10000).")
            return self.config.ASK_CAPITAL
    
    async def ask_target_handler(self, update, context):
        """Handle stoploss input and ask for target."""
        try:
            sl_percent = parse_percentage(update.message.text.strip())
            context.user_data["sl"] = sl_percent
            
            # Save SL to preferences
            self.config.save_user_preferences(sl_percent=sl_percent)
            
            await update.message.reply_text("🎯 Enter Target % (e.g., 0.6 or 0.6%)")
            return self.config.ASK_TARGET
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid SL: {e}")
            return self.config.ASK_SL
    
    async def ready_handler(self, update, context):
        """Handle target input and mark as ready."""
        try:
            target_percent = parse_percentage(update.message.text.strip())
            context.user_data["target"] = target_percent
            
            # Save target to preferences
            self.config.save_user_preferences(target_percent=target_percent)
            
            await update.message.reply_text("✅ Setup complete! Now send me a stock name or symbol.")
            return self.config.READY
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid Target: {e}")
            return self.config.ASK_TARGET
    
    async def handle_symbol_input(self, update, context):
        """Handle symbol input and place orders."""
        # Load preferences if not already loaded (for both direct messages and channels)
        if not context.user_data.get("capital"):
            if self.config.has_complete_preferences():
                context.user_data["capital"] = self.config.user_preferences.get("capital")
                context.user_data["sl"] = self.config.user_preferences.get("sl_percent")
                context.user_data["target"] = self.config.user_preferences.get("target_percent")
            else:
                await update.message.reply_text(
                    "❌ Trading settings not configured!\n\n"
                    "Please use /start to set up your trading parameters first.",
                    parse_mode='Markdown'
                )
                return
        
        telegram_message = update.message.text.strip()
        print(f"💬 User sent: {telegram_message}")

        # Check if we're in trade management mode
        if context.user_data.get("in_modify_mode", False):
            # This is a trade selection, not a symbol search
            return await self.handle_trade_selection(update, context)
        
        # Check if we're in modification states but user sent a symbol
        current_state = context.user_data.get("conversation_state")
        if current_state in [self.config.MODIFY_SL, self.config.MODIFY_TARGET, self.config.MODIFY_ENTRY_PRICE]:
            # User sent a symbol while in modification mode, clear the mode and process as symbol
            context.user_data.pop("in_modify_mode", None)
            context.user_data.pop("selected_trade_id", None)
            context.user_data.pop("conversation_state", None)
            await update.message.reply_text("🔄 Cleared modification mode. Processing as new symbol search...")
        
        # Check if user is trying to use /m command while in modify mode
        if context.user_data.get("in_modify_mode", False) and telegram_message == "/m":
            await update.message.reply_text("🔄 Already in modify mode. Please select an option or use /reset to clear.")
            return

        # Check if it's a previously searched symbol
        last_symbols = context.user_data.get("last_symbols", {})
        if telegram_message in last_symbols:
            stock = last_symbols[telegram_message]
            exch, token = stock["exch"], stock["token"]
            
            # Store selected symbol info
            context.user_data["selected_symbol"] = telegram_message
            context.user_data["selected_exch"] = exch
            context.user_data["selected_token"] = token
            
            # Subscribe to symbol for real-time data
            self.api_client.subscribe_symbol(exch, token)
            
            # Show order type selection
            keyboard = [
                ["📈 Market Order", "🎯 Limit Order"],
                ["❌ Cancel"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await update.message.reply_text(
                f"📌 Selected: {telegram_message}\n\n"
                f"Choose order type:",
                reply_markup=reply_markup
            )
            return self.config.ORDER_TYPE_SELECTION

        # Search for new symbol
        # Try different search approaches
        data = None
        search_attempts = [
            ("NSE", telegram_message),
            ("NSE", telegram_message.upper()),
            ("NSE", telegram_message.lower()),
            ("BSE", telegram_message),
            ("BSE", telegram_message.upper()),
        ]
        
        for exchange, search_text in search_attempts:
            data = self.api_client.search_symbol(exchange, search_text)
            if data and "values" in data and data["values"]:
                break
        
        if not data or "values" not in data or not data["values"]:
            await update.message.reply_text("❌ No matching symbols found. Try searching with the full company name or symbol.")
            return

        # Create symbol selection keyboard
        stock_map = {item["tsym"]: {"exch": item["exch"], "token": item["token"]}
                     for item in data["values"]}
        context.user_data["last_symbols"] = stock_map

        keyboard = [[tsym] for tsym in stock_map.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text("✅ Choose a symbol:", reply_markup=reply_markup)
    
    async def status_command(self, update, context):
        """Handle /status command to show active trades."""
        stats = self.trading_engine.get_trade_statistics()
        active_trades_info = self.trading_engine.get_active_trades_info()
        
        status_msg = (
            f"📊 Trading Status\n\n"
            f"💰 Total PnL: {stats['total_pnl']}\n"
            f"📈 Active Trades: {stats['active_trades']}\n"
            f"📋 Total Trades: {stats['total_trades']}\n\n"
            f"{active_trades_info}"
        )
        
        await update.message.reply_text(status_msg)
    
    async def trades_command(self, update, context):
        """Handle /trades command to show active trades with current PnL."""
        trades_with_pnl = self.trading_engine.get_active_trades_with_pnl()
        
        if not trades_with_pnl:
            await update.message.reply_text("📊 No active trades found.")
            return
        
        # Calculate total current PnL
        total_current_pnl = 0
        valid_trades = 0
        
        trades_msg = "📊 **Active Trades with Current PnL**\n\n"
        
        for trade in trades_with_pnl:
            if trade["current_pnl"] != "N/A":
                total_current_pnl += trade["current_pnl"]
                valid_trades += 1
                
                # Format PnL with color emoji
                pnl_emoji = "📈" if trade["current_pnl"] >= 0 else "📉"
                pnl_color = "🟢" if trade["current_pnl"] >= 0 else "🔴"
                
                trades_msg += (
                    f"{pnl_color} **{trade['symbol']}**\n"
                    f"🆔 Order: `{trade['order_id']}`\n"
                    f"💰 Entry: ₹{trade['entry_price']}\n"
                    f"📊 Current: ₹{trade['current_price']}\n"
                    f"📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n"
                    f"📦 Qty: {trade['qty']}\n"
                    f"{pnl_emoji} PnL: ₹{trade['current_pnl']} ({trade['current_pnl_pct']}%)\n"
                    f"⏰ Entry Time: {trade['entry_time']}\n\n"
                )
            else:
                trades_msg += (
                    f"⚠️ **{trade['symbol']}**\n"
                    f"🆔 Order: `{trade['order_id']}`\n"
                    f"💰 Entry: ₹{trade['entry_price']}\n"
                    f"📊 Current: {trade['current_price']}\n"
                    f"📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n"
                    f"📦 Qty: {trade['qty']}\n"
                    f"❌ PnL: Unable to calculate\n"
                    f"⏰ Entry Time: {trade['entry_time']}\n\n"
                )
        
        # Add summary
        if valid_trades > 0:
            total_emoji = "📈" if total_current_pnl >= 0 else "📉"
            trades_msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            trades_msg += f"{total_emoji} **Total Current PnL: ₹{total_current_pnl:.2f}**\n"
            trades_msg += f"📊 **Active Trades: {len(trades_with_pnl)}**"
        else:
            trades_msg += f"⚠️ **Unable to calculate PnL for any trades**"
        
        await update.message.reply_text(trades_msg, parse_mode='Markdown')
    
    async def modify_command(self, update, context):
        """Handle /m command for trade management."""
        trades_list = self.trading_engine.get_active_trades_list()
        
        if not trades_list:
            await update.message.reply_text("📊 No active trades found.")
            return
        
        # Set modify mode flag
        context.user_data["in_modify_mode"] = True
        
        # Create keyboard with active trades
        keyboard = [[trade_display] for trade_display in trades_list.keys()]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "📊 Select a trade to modify:",
            reply_markup=reply_markup
        )
        return self.config.TRADE_SELECTION
    
    async def handle_trade_selection(self, update, context):
        """Handle trade selection from the list."""
        selected_trade = update.message.text.strip()
        trades_list = self.trading_engine.get_active_trades_list()
        
        if selected_trade not in trades_list:
            await update.message.reply_text("❌ Invalid trade selection. Please try again.")
            return self.config.TRADE_SELECTION
        
        # Store selected trade ID
        selected_trade_id = trades_list[selected_trade]
        context.user_data["selected_trade_id"] = selected_trade_id
        
        # Show modify options based on order status
        trade = self.trading_engine.active_trades[selected_trade_id]
        order_status = trade.get("order_status", "UNKNOWN")
        
        print(f"🔧 Trade selected: {selected_trade_id}, Status: {order_status}")
        
        if order_status == "PENDING":
            # For pending orders, show different options
            keyboard = [
                ["💰 Modify Entry Price", "❌ Cancel Order"],
                ["📉 Modify SL", "🎯 Modify Target"],
                ["🚪 Exit Trade", "❌ Back"]
            ]
        else:
            # For filled orders, show regular options
            keyboard = [
                ["📉 Modify SL", "🎯 Modify Target"],
                ["🚪 Exit Trade", "❌ Cancel"]
            ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🔧 What would you like to do with this trade?\n\n{selected_trade}",
            reply_markup=reply_markup
        )
        
        # Set modify mode flag
        context.user_data["in_modify_mode"] = True
        
        return self.config.MODIFY_OPTIONS
    
    async def handle_modify_options(self, update, context):
        """Handle modify options selection."""
        option = update.message.text.strip()
        trade_id = context.user_data.get("selected_trade_id")
        
        print(f"🔧 Modify options handler called with option: {option}, trade_id: {trade_id}")
        
        if not trade_id:
            await update.message.reply_text("❌ No trade selected. Use /m to start again.")
            return
        
        if option == "📉 Modify SL":
            await update.message.reply_text(
                "📉 Enter new Stoploss % (e.g., 0.5 or 0.5%)\n\n"
                "Current trade will be updated with new SL."
            )
            return self.config.MODIFY_SL
        
        elif option == "🎯 Modify Target":
            await update.message.reply_text(
                "🎯 Enter new Target % (e.g., 1.0 or 1.0%)\n\n"
                "Current trade will be updated with new target."
            )
            return self.config.MODIFY_TARGET
        
        elif option == "💰 Modify Entry Price":
            # Get current limit price for reference
            trade = self.trading_engine.active_trades[trade_id]
            current_price = trade.get('limit_price', 'N/A')
            
            await update.message.reply_text(
                f"💰 Enter new limit price for {trade['symbol']}:\n\n"
                f"📊 Current Limit Price: ₹{current_price}\n"
                f"💡 Enter your new limit price (e.g., {current_price})"
            )
            return self.config.MODIFY_ENTRY_PRICE
        
        elif option == "❌ Cancel Order":
            success, message = await self.trading_engine.cancel_order(trade_id, context)
            # Clear modify mode flag
            context.user_data.pop("in_modify_mode", None)
            context.user_data.pop("selected_trade_id", None)
            await update.message.reply_text(message)
            return self.config.READY
        
        elif option == "🚪 Exit Trade":
            success, message = await self.trading_engine.manual_exit_trade(trade_id, context)
            # Clear modify mode flag
            context.user_data.pop("in_modify_mode", None)
            context.user_data.pop("selected_trade_id", None)
            await update.message.reply_text(message)
            return self.config.READY
        
        elif option in ["❌ Cancel", "❌ Back"]:
            # Clear modify mode flag
            context.user_data.pop("in_modify_mode", None)
            context.user_data.pop("selected_trade_id", None)
            await update.message.reply_text("❌ Trade modification cancelled.")
            return self.config.READY
        
        else:
            await update.message.reply_text("❌ Invalid option. Please try again.")
            return self.config.MODIFY_OPTIONS
    
    async def handle_sl_modification(self, update, context):
        """Handle SL modification input."""
        try:
            new_sl_percent = parse_percentage(update.message.text.strip())
            trade_id = context.user_data.get("selected_trade_id")
            
            if not trade_id:
                await update.message.reply_text("❌ No trade selected. Use /m to start again.")
                return
            
            success, message = self.trading_engine.update_trade_sl(trade_id, new_sl_percent)
            await update.message.reply_text(message)
            
            # Clear selected trade and modify mode
            context.user_data.pop("selected_trade_id", None)
            context.user_data.pop("in_modify_mode", None)
            
            # Return to READY state for new trades
            return self.config.READY
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid SL percentage: {e}")
            return self.config.MODIFY_SL
    
    async def handle_target_modification(self, update, context):
        """Handle target modification input."""
        try:
            new_target_percent = parse_percentage(update.message.text.strip())
            trade_id = context.user_data.get("selected_trade_id")
            
            if not trade_id:
                await update.message.reply_text("❌ No trade selected. Use /m to start again.")
                return
            
            success, message = self.trading_engine.update_trade_target(trade_id, new_target_percent)
            await update.message.reply_text(message)
            
            # Clear selected trade and modify mode
            context.user_data.pop("selected_trade_id", None)
            context.user_data.pop("in_modify_mode", None)
            
            # Return to READY state for new trades
            return self.config.READY
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid target percentage: {e}")
            return self.config.MODIFY_TARGET
    
    async def handle_entry_price_modification(self, update, context):
        """Handle entry price modification input."""
        try:
            new_limit_price = float(update.message.text.strip())
            trade_id = context.user_data.get("selected_trade_id")
            
            if not trade_id:
                await update.message.reply_text("❌ No trade selected. Use /m to start again.")
                return
            
            success, message = await self.trading_engine.modify_limit_price(trade_id, new_limit_price, context)
            await update.message.reply_text(message)
            
            # Clear selected trade and modify mode
            context.user_data.pop("selected_trade_id", None)
            context.user_data.pop("in_modify_mode", None)
            
            # Return to READY state for new trades
            return self.config.READY
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid price: {e}\n\nPlease enter a valid number (e.g., 467.50)")
            return self.config.MODIFY_ENTRY_PRICE
        except Exception as e:
            await update.message.reply_text(f"❌ Modification failed: {e}")
            return self.config.MODIFY_ENTRY_PRICE
    
    async def handle_order_type_selection(self, update, context):
        """Handle order type selection (Market vs Limit)."""
        order_type = update.message.text.strip()
        
        if order_type == "📈 Market Order":
            # Place market order directly
            symbol = context.user_data.get("selected_symbol")
            exch = context.user_data.get("selected_exch")
            token = context.user_data.get("selected_token")
            
            if not all([symbol, exch, token]):
                await update.message.reply_text("❌ Symbol information not found. Please try again.")
                return
            
            await update.message.reply_text(f"📌 Placing Market Order for {symbol}...")
            
            order_resp, msg = self.trading_engine.place_long_order(
                symbol, exch, token,
                context.user_data["capital"],
                context.user_data["sl"],
                context.user_data["target"],
                context,
                order_type="MKT"
            )
            await update.message.reply_text(msg)
            
            # Clear selected symbol data
            context.user_data.pop("selected_symbol", None)
            context.user_data.pop("selected_exch", None)
            context.user_data.pop("selected_token", None)
            
            # Return to READY state for new trades
            return self.config.READY
            
        elif order_type == "🎯 Limit Order":
            # Get current LTP for the selected symbol
            symbol = context.user_data.get("selected_symbol")
            exch = context.user_data.get("selected_exch")
            token = context.user_data.get("selected_token")
            
            if not all([symbol, exch, token]):
                await update.message.reply_text("❌ Symbol information not found. Please try again.")
                return
            
            # Subscribe to symbol for real-time updates
            self.api_client.subscribe_symbol(exch, token)
            
            # Get current quote
            quote = self.api_client.get_quote(exch, token)
            
            if not quote or "lp" not in quote:
                await update.message.reply_text(
                    f"❌ Unable to fetch current LTP for {symbol}.\n"
                    f"Please try again or use Market Order instead."
                )
                return
            
            current_ltp = f"₹{quote['lp']}"
            
            # Ask for limit price with current LTP
            await update.message.reply_text(
                f"🎯 Enter limit price for {symbol}:\n\n"
                f"📊 Current LTP: {current_ltp}\n"
                f"💡 Enter your desired limit price (e.g., {current_ltp.replace('₹', '')})"
            )
            return self.config.LIMIT_PRICE_INPUT
            
        elif order_type == "❌ Cancel":
            await update.message.reply_text("❌ Order cancelled.")
            # Clear selected symbol data
            context.user_data.pop("selected_symbol", None)
            context.user_data.pop("selected_exch", None)
            context.user_data.pop("selected_token", None)
            # Return to READY state for new trades
            return self.config.READY
        else:
            await update.message.reply_text("❌ Invalid selection. Please choose Market Order or Limit Order.")
            return self.config.ORDER_TYPE_SELECTION
    
    async def handle_limit_price_input(self, update, context):
        """Handle limit price input."""
        try:
            limit_price = float(update.message.text.strip())
            
            symbol = context.user_data.get("selected_symbol")
            exch = context.user_data.get("selected_exch")
            token = context.user_data.get("selected_token")
            
            if not all([symbol, exch, token]):
                await update.message.reply_text("❌ Symbol information not found. Please try again.")
                return
            
            await update.message.reply_text(f"📌 Placing Limit Order for {symbol} @ ₹{limit_price}...")
            
            order_resp, msg = self.trading_engine.place_long_order(
                symbol, exch, token,
                context.user_data["capital"],
                context.user_data["sl"],
                context.user_data["target"],
                context,
                order_type="LMT",
                limit_price=limit_price
            )
            await update.message.reply_text(msg)
            
            # Clear selected symbol data
            context.user_data.pop("selected_symbol", None)
            context.user_data.pop("selected_exch", None)
            context.user_data.pop("selected_token", None)
            
            # Return to READY state for new trades
            return self.config.READY
            
        except ValueError:
            await update.message.reply_text("❌ Invalid price. Please enter a valid number (e.g., 1500.50)")
            return self.config.LIMIT_PRICE_INPUT

    async def search_command(self, update, context):
        """Handle /s or /search command to return to trading mode."""
        # Check if user has already set up trading parameters
        if "capital" in context.user_data and "sl" in context.user_data and "target" in context.user_data:
            await update.message.reply_text(
                "✅ Ready for trading! Send me a stock name or symbol.\n\n"
                f"💰 Capital: ₹{context.user_data['capital']}\n"
                f"📉 SL: {context.user_data['sl']}%\n"
                f"🎯 Target: {context.user_data['target']}%"
            )
            return self.config.READY
        else:
            await update.message.reply_text(
                "⚠️ Trading parameters not set. Please use /start to configure your trading setup first."
            )
            return

    async def recover_command(self, update, context):
        """Handle /recover command to recover orphaned trades."""
        try:
            # Parse the recovery command: /recover SYMBOL ENTRY_PRICE SL% TARGET%
            command_parts = update.message.text.strip().split()
            
            if len(command_parts) != 5:
                await update.message.reply_text(
                    "❌ Invalid recovery command format.\n\n"
                    "Usage: /recover SYMBOL ENTRY_PRICE SL% TARGET%\n\n"
                    "Example: /recover CARYSIL-EQ 967.2 0.5 1.0"
                )
                return
            
            symbol = command_parts[1]
            entry_price = float(command_parts[2])
            sl_percent = float(command_parts[3])
            target_percent = float(command_parts[4])
            
            # Get entry time from trade log
            entry_time = None
            try:
                with open(self.trading_engine.trade_logger.log_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['Symbol'] == symbol and float(row['EntryPrice']) == entry_price:
                            entry_time = row['EntryTime']
                            break
            except Exception as e:
                print(f"Error reading trade log: {e}")
            
            if not entry_time:
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Recover the trade
            success, message = await self.trading_engine.recover_orphaned_trade(
                symbol, entry_price, entry_time, sl_percent, target_percent, context
            )
            
            await update.message.reply_text(message)
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid input: {e}\n\nUsage: /recover SYMBOL ENTRY_PRICE SL% TARGET%")
        except Exception as e:
            await update.message.reply_text(f"❌ Recovery failed: {e}")

    async def reset_command(self, update, context):
        """Handle /reset command to clear conversation state."""
        # Clear all conversation state
        context.user_data.clear()
        
        await update.message.reply_text(
            "🔄 Conversation state reset!\n\n"
            "✅ All modification modes cleared\n"
            "✅ Ready for new trading session\n\n"
            "Use /start to begin trading setup or /s to return to trading mode."
        )
        return self.config.READY

    async def help_command(self, update, context):
        """Handle /help command."""
        help_msg = (
            "🤖 Trading Bot Commands:\n\n"
            "/start - Start trading setup\n"
            "/s or /search - Return to trading mode (if already configured)\n"
            "/status - View trading statistics\n"
            "/trades - View active trades with current PnL\n"
            "/m - Modify active trades (SL, Target, Exit)\n"
            "/recover - Recover orphaned trades\n"
            "/reset - Reset conversation state (if stuck)\n"
            "/help - Show this help message\n\n"
            "📝 How to use:\n"
            "1. Send /start to begin\n"
            "2. Enter your trading capital\n"
            "3. Set stoploss percentage\n"
            "4. Set target percentage\n"
            "5. Send stock symbol to trade\n"
            "6. Choose order type (Market or Limit)\n"
            "7. For limit orders, enter limit price\n\n"
            "🔧 Trade Management:\n"
            "• Use /trades to view active trades with PnL\n"
            "• Use /m to modify active trades\n"
            "• Use /s to quickly return to trading mode\n"
            "• Select trade from list\n"
            "• Choose to modify SL, Target, or Exit\n"
            "• Use /cleanup to clean up old persisted trades\n\n"
            "🔄 Recovery:\n"
            "• Use /recover SYMBOL ENTRY_PRICE SL% TARGET%\n"
            "• Example: /recover CARYSIL-EQ 967.2 0.5 1.0\n\n"
            "🚨 Troubleshooting:\n"
            "• Use /reset if bot gets stuck in modification mode\n"
            "• Use /s to return to trading mode anytime"
        )
        
        await update.message.reply_text(help_msg)
    
    async def button_callback(self, update, context):
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "continue_trading":
            # Load saved preferences into context
            context.user_data["capital"] = self.config.user_preferences.get("capital")
            context.user_data["sl"] = self.config.user_preferences.get("sl_percent")
            context.user_data["target"] = self.config.user_preferences.get("target_percent")
            
            await query.edit_message_text(
                "✅ **Trading Ready!**\n\n"
                "📊 Using your saved settings:\n"
                f"💰 Capital: ₹{context.user_data['capital']:,.0f}\n"
                f"📉 SL: {context.user_data['sl']}%\n"
                f"🎯 Target: {context.user_data['target']}%\n\n"
                "🎯 Now send me a stock name or symbol to trade!",
                parse_mode='Markdown'
            )
            return self.config.READY
            
        elif query.data == "modify_settings":
            await query.edit_message_text(
                "⚙️ **Modify Settings**\n\n"
                "Let's update your trading parameters:\n\n"
                "💰 How much capital do you want to trade with?",
                parse_mode='Markdown'
            )
            return self.config.ASK_CAPITAL
            
        elif query.data == "view_trades":
            # Show active trades
            trades_with_pnl = self.trading_engine.get_active_trades_with_pnl()
            
            if not trades_with_pnl:
                await query.edit_message_text("📊 No active trades found.")
                return self.config.READY
            
            # Calculate total current PnL
            total_current_pnl = 0
            valid_trades = 0
            
            trades_msg = "📊 **Active Trades with Current PnL**\n\n"
            
            for trade in trades_with_pnl:
                if trade["current_pnl"] != "N/A":
                    total_current_pnl += trade["current_pnl"]
                    valid_trades += 1
                    
                    # Format PnL with color emoji
                    pnl_emoji = "📈" if trade["current_pnl"] >= 0 else "📉"
                    pnl_color = "🟢" if trade["current_pnl"] >= 0 else "🔴"
                    
                    trades_msg += (
                        f"{pnl_color} **{trade['symbol']}**\n"
                        f"🆔 Order: `{trade['order_id']}`\n"
                        f"💰 Entry: ₹{trade['entry_price']}\n"
                        f"📊 Current: ₹{trade['current_price']}\n"
                        f"📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n"
                        f"📦 Qty: {trade['qty']}\n"
                        f"{pnl_emoji} PnL: ₹{trade['current_pnl']} ({trade['current_pnl_pct']}%)\n"
                        f"⏰ Entry Time: {trade['entry_time']}\n\n"
                    )
                else:
                    trades_msg += (
                        f"⚪ **{trade['symbol']}**\n"
                        f"🆔 Order: `{trade['order_id']}`\n"
                        f"💰 Entry: ₹{trade['entry_price']}\n"
                        f"📊 Current: N/A\n"
                        f"📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n"
                        f"📦 Qty: {trade['qty']}\n"
                        f"⏰ Entry Time: {trade['entry_time']}\n\n"
                    )
            
            if valid_trades > 0:
                avg_pnl = total_current_pnl / valid_trades
                trades_msg += f"📊 **Total PnL:** ₹{total_current_pnl:.2f}\n"
                trades_msg += f"📈 **Average PnL:** ₹{avg_pnl:.2f}\n"
                trades_msg += f"🔢 **Active Trades:** {len(trades_with_pnl)}"
            
            await query.edit_message_text(trades_msg, parse_mode='Markdown')
            return self.config.READY
            
        elif query.data == "search_symbol":
            await query.edit_message_text(
                "🔍 **Symbol Search**\n\n"
                "Enter a stock name or symbol to search:\n"
                "• Company name (e.g., 'Reliance')\n"
                "• Symbol (e.g., 'RELIANCE')\n"
                "• Partial name (e.g., 'TCS')\n\n"
                "I'll find the best matches for you!",
                parse_mode='Markdown'
            )
            return self.config.READY
    
    async def cleanup_command(self, update, context):
        """Handle /cleanup command to clean up old persisted trades."""
        try:
            # Clean up persisted trades file
            self.trading_engine.cleanup_persisted_trades()
            
            cleanup_msg = (
                "🧹 **Cleanup Complete!**\n\n"
                "✅ Removed old persisted trades file\n"
                "🔄 Active trades are still being monitored\n"
                "💡 Use /trades to view current status"
            )
            
            await update.message.reply_text(cleanup_msg)
            
        except Exception as e:
            error_msg = f"❌ Cleanup failed: {e}"
            await update.message.reply_text(error_msg)
    
    def setup_handlers(self):
        """Setup all bot handlers."""
        # Single conversation handler for both trading and modification
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start_command),
                CommandHandler("m", self.modify_command)
            ],
            states={
                # Trading states
                self.config.ASK_CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_sl_handler)],
                self.config.ASK_SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ask_target_handler)],
                self.config.ASK_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.ready_handler)],
                self.config.READY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_symbol_input),
                    CallbackQueryHandler(self.button_callback)
                ],
                
                # Order type states
                self.config.ORDER_TYPE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_order_type_selection)],
                self.config.LIMIT_PRICE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_limit_price_input)],
                
                # Trade management states
                self.config.TRADE_SELECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_trade_selection)],
                self.config.MODIFY_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_modify_options)],
                self.config.MODIFY_SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_sl_modification)],
                self.config.MODIFY_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_target_modification)],
                self.config.MODIFY_ENTRY_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_entry_price_modification)],
            },
            fallbacks=[
                CommandHandler("start", self.start_command),
                CommandHandler("m", self.modify_command)
            ],
        )
        
        # Add all handlers
        self.app.add_handler(conv_handler)
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("trades", self.trades_command))
        self.app.add_handler(CommandHandler("s", self.search_command))
        self.app.add_handler(CommandHandler("search", self.search_command))
        self.app.add_handler(CommandHandler("recover", self.recover_command))
        self.app.add_handler(CommandHandler("reset", self.reset_command))
        self.app.add_handler(CommandHandler("cleanup", self.cleanup_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Channel support is integrated into the conversation handler
    
    def start_bot(self):
        """Start the telegram bot."""
        self.app = ApplicationBuilder().token(self.config.BOT_TOKEN).build()
        self.setup_handlers()
        print("🤖 Starting Telegram Bot...")
        
        # Skip startup notification to avoid event loop conflicts
        print("ℹ️ Bot ready for direct messages - send /start to begin")
        
        # Add error handling for conflicts
        try:
            self.app.run_polling(
                drop_pending_updates=True,  # Drop any pending updates to avoid conflicts
                allowed_updates=None,  # Allow all update types
                close_loop=False  # Don't close the event loop
            )
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user (Ctrl+C)")
            self._cleanup()
        except Exception as e:
            if "Conflict" in str(e):
                print("❌ Telegram bot conflict detected. Another instance may be running.")
                print("💡 Please wait a moment and try again, or check for other running instances.")
                print("💡 You can use 'taskkill /f /im python.exe' to stop all Python processes.")
            else:
                print(f"❌ Telegram bot error: {e}")
            self._cleanup()
            raise
    
    def _cleanup(self):
        """Clean up resources before shutdown."""
        try:
            if self.app:
                print("🧹 Cleaning up bot resources...")
                # Stop the bot gracefully
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(self.app.stop())
                    else:
                        loop.run_until_complete(self.app.stop())
                except:
                    # If event loop issues, just continue
                    pass
                print("✅ Bot cleanup completed")
        except Exception as e:
            print(f"⚠️ Error during cleanup: {e}")
    
    async def _send_startup_notification_async(self):
        """Send startup notification asynchronously after bot starts."""
        try:
            # Wait a moment for bot to fully initialize
            await asyncio.sleep(2)
            await self.send_startup_notification()
        except Exception as e:
            print(f"❌ Error sending startup notification: {e}")
    
    def _restore_trade_contexts(self, update, context):
        """Restore context for recovered trades when user interacts with bot."""
        try:
            trades_needing_context = self.trading_engine.get_trades_needing_context()
            if trades_needing_context:
                print(f"🔄 Restoring context for {len(trades_needing_context)} recovered trades")
                
                # Update context for all trades that need it
                for order_id in trades_needing_context:
                    self.trading_engine.update_trade_context(order_id, context)
                
                # Send notification about recovered trades
                recovery_msg = (
                    f"🔄 **Trade Recovery Complete!**\n\n"
                    f"✅ Restored context for {len(trades_needing_context)} active trades\n"
                    f"📊 These trades are now being monitored for SL/Target\n"
                    f"💡 Use /trades to view current status"
                )
                
                # Send notification to user (synchronously)
                try:
                    if self.app and self.app.bot and update.effective_chat:
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.app.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=recovery_msg,
                            parse_mode='Markdown'
                        ))
                        loop.close()
                except Exception as e:
                    print(f"❌ Error sending recovery notification: {e}")
                
        except Exception as e:
            print(f"❌ Error restoring trade contexts: {e}")
    
    def _get_active_trades_summary(self):
        """Get a summary of active trades for the welcome message."""
        try:
            trades_with_pnl = self.trading_engine.get_active_trades_with_pnl()
            
            if not trades_with_pnl:
                return "📊 **Active Trades:** None\n"
            
            # Calculate summary statistics
            total_pnl = 0
            valid_trades = 0
            pending_trades = 0
            completed_trades = 0
            
            trades_summary = "📊 **Active Trades:**\n"
            
            for trade in trades_with_pnl:
                order_id = trade['order_id']
                active_trade = self.trading_engine.active_trades.get(order_id, {})
                order_status = active_trade.get('order_status', 'UNKNOWN')
                
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
                    
                    trades_summary += (
                        f"{status_emoji} **{trade['symbol']}** {pnl_color}\n"
                        f"   💰 Entry: ₹{trade['entry_price']} → Current: ₹{trade['current_price']}\n"
                        f"   {pnl_emoji} PnL: ₹{trade['current_pnl']} ({trade['current_pnl_pct']}%)\n"
                        f"   📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n\n"
                    )
                else:
                    status_emoji = "⏳" if order_status == 'PENDING' else "✅" if order_status == 'COMPLETE' else "❓"
                    
                    trades_summary += (
                        f"{status_emoji} **{trade['symbol']}** ⚪\n"
                        f"   💰 Entry: ₹{trade['entry_price']} → Current: N/A\n"
                        f"   📉 SL: ₹{trade['sl']} | 🎯 Target: ₹{trade['tgt']}\n\n"
                    )
            
            # Add summary statistics
            if valid_trades > 0:
                avg_pnl = total_pnl / valid_trades
                trades_summary += f"📊 **Summary:** Total PnL: ₹{total_pnl:.2f} | Avg: ₹{avg_pnl:.2f}\n"
            
            trades_summary += f"🔢 **Count:** {len(trades_with_pnl)} total"
            if pending_trades > 0:
                trades_summary += f" | {pending_trades} pending"
            if completed_trades > 0:
                trades_summary += f" | {completed_trades} filled"
            
            return trades_summary
            
        except Exception as e:
            print(f"❌ Error getting active trades summary: {e}")
            return "📊 **Active Trades:** Error loading trades\n"
    
    def _get_websocket_status(self):
        """Get websocket monitoring status for the welcome message."""
        try:
            active_trades_count = len(self.trading_engine.active_trades)
            
            if active_trades_count == 0:
                return "📡 **Monitoring:** No active trades to monitor\n"
            
            # Check how many trades have valid exchange and token data
            monitorable_trades = 0
            for trade in self.trading_engine.active_trades.values():
                if 'exch' in trade and 'token' in trade:
                    monitorable_trades += 1
            
            if monitorable_trades == active_trades_count:
                return f"📡 **Monitoring:** {monitorable_trades} trades via websocket ✅\n"
            elif monitorable_trades > 0:
                return f"📡 **Monitoring:** {monitorable_trades}/{active_trades_count} trades via websocket ⚠️\n"
            else:
                return f"📡 **Monitoring:** {active_trades_count} trades (no websocket data) ❌\n"
                
        except Exception as e:
            print(f"❌ Error getting websocket status: {e}")
            return "📡 **Monitoring:** Status unknown\n"
    
    async def send_startup_notification(self):
        """Send startup notification to Telegram with current parameters and trades."""
        try:
            # Check if app is initialized
            if not self.app or not self.app.bot:
                print("⚠️ Telegram bot not initialized, skipping startup notification")
                return
                
            # Get channel ID from config
            channel_id = self.config.TELEGRAM_CHANNEL_ID
            if not channel_id or channel_id.strip() == "":
                print("ℹ️ No Telegram channel configured, bot ready for direct messages")
                return
            
            # Build startup message
            startup_msg = self._build_startup_message()
            
            # Send notification to channel
            await self.app.bot.send_message(
                chat_id=channel_id,
                text=startup_msg,
                parse_mode='Markdown'
            )
            
            print("✅ Startup notification sent to Telegram")
            
        except Exception as e:
            print(f"❌ Error sending startup notification: {e}")
    
    def _build_startup_message(self):
        """Build comprehensive startup message."""
        try:
            # Bot status
            status_msg = "🚀 **Order Executor Bot Started Successfully!**\n"
            status_msg += f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            status_msg += "=" * 50 + "\n\n"
            
            # User preferences
            if self.config.has_complete_preferences():
                preferences_summary = self.config.get_preferences_summary()
                status_msg += f"📊 **Your Trading Settings:**\n{preferences_summary}\n\n"
            else:
                status_msg += "📊 **Trading Settings:** Not configured\n\n"
            
            # Trade recovery status
            trades_needing_context = self.trading_engine.get_trades_needing_context()
            if trades_needing_context:
                status_msg += f"🔄 **Trade Recovery:** {len(trades_needing_context)} trades restored\n"
                status_msg += "💡 Context will be restored when you interact with the bot\n\n"
            else:
                status_msg += "🔄 **Trade Recovery:** No trades needed restoration\n\n"
            
            # Active trades
            active_trades_info = self._get_active_trades_summary()
            status_msg += active_trades_info + "\n"
            
            # Websocket status
            websocket_status = self._get_websocket_status()
            status_msg += websocket_status + "\n"
            
            # System status
            status_msg += "🔧 **System Status:**\n"
            status_msg += "✅ API Connection: Active\n"
            status_msg += "✅ WebSocket: Connected\n"
            status_msg += "✅ Trade Monitoring: Enabled\n"
            status_msg += "✅ Notifications: Enabled\n\n"
            
            # Quick actions
            status_msg += "🎯 **Quick Actions:**\n"
            status_msg += "• Send any symbol to start trading\n"
            status_msg += "• Use /trades to view detailed PnL\n"
            status_msg += "• Use /m to modify existing trades\n"
            status_msg += "• Use /help for all commands\n\n"
            
            # Footer
            status_msg += "🤖 **Bot is ready to accept trades!**"
            
            return status_msg
            
        except Exception as e:
            print(f"❌ Error building startup message: {e}")
            return "🚀 **Order Executor Bot Started!**\n\n❌ Error loading details. Use /help for commands."
    
