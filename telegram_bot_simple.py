"""
Simplified Telegram bot for Order Executor trading bot.
This version removes async complexity to get back to working state.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from config import Config
import asyncio


class TelegramBot:
    """Simplified Telegram bot for trading operations."""
    
    def __init__(self, config, api_client, trading_engine):
        self.config = config
        self.api_client = api_client
        self.trading_engine = trading_engine
        self.app = None
    
    def start_command(self, update, context):
        """Handle /start command."""
        # Restore context for any recovered trades
        self._restore_trade_contexts(update, context)
        
        # Check if user has saved preferences
        if self.config.has_complete_preferences():
            # Show saved preferences with inline buttons
            preferences_summary = self.config.get_preferences_summary()
            
            # Get active trades information
            active_trades_summary = self._get_active_trades_summary()
            
            welcome_msg = (
                f"🤖 **Order Executor Bot**\n\n"
                f"{preferences_summary}\n"
                f"{active_trades_summary}\n"
                f"💡 **Commands:**\n"
                f"• Send stock name/symbol to trade\n"
                f"• /trades - View active trades\n"
                f"• /m - Modify existing trades\n"
                f"• /help - Show all commands"
            )
            
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 View Trades", callback_data="view_trades")],
                [InlineKeyboardButton("⚙️ Modify Trades", callback_data="modify_trades")],
                [InlineKeyboardButton("❓ Help", callback_data="help")]
            ])
            
            update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            update.message.reply_text("👋 Welcome! How much capital do you want to trade with?")
            return self.config.ASK_CAPITAL
    
    def _restore_trade_contexts(self, update, context):
        """Restore context for recovered trades when user interacts with bot."""
        try:
            trades_needing_context = self.trading_engine.get_trades_needing_context()
            if trades_needing_context:
                print(f"🔄 Restoring context for {len(trades_needing_context)} recovered trades")
                
                # Update context for all trades that need it
                for order_id in trades_needing_context:
                    self.trading_engine.update_trade_context(order_id, context)
                
                print(f"✅ Restored context for {len(trades_needing_context)} trades")
                
        except Exception as e:
            print(f"❌ Error restoring trade contexts: {e}")
    
    def _get_active_trades_summary(self):
        """Get a summary of active trades for the welcome message."""
        try:
            trades_with_pnl = self.trading_engine.get_active_trades_with_pnl()
            
            if not trades_with_pnl:
                return "📊 **Active Trades:** None\n"
            
            summary_lines = ["📊 **Active Trades:**"]
            for trade in trades_with_pnl:
                symbol = trade.get('symbol', 'Unknown')
                qty = trade.get('qty', 0)
                entry_price = trade.get('entry_price', 0.0)
                current_price = trade.get('current_price', 0.0)
                pnl = trade.get('pnl', 0.0)
                pnl_pct = trade.get('pnl_percentage', 0.0)
                
                status_emoji = "🟢" if pnl >= 0 else "🔴"
                summary_lines.append(
                    f"{status_emoji} {symbol}: {qty} @ ₹{entry_price:.2f} "
                    f"(LTP: ₹{current_price:.2f}, P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%))"
                )
            
            return "\n".join(summary_lines) + "\n"
            
        except Exception as e:
            print(f"❌ Error getting active trades summary: {e}")
            return "📊 **Active Trades:** Status unknown\n"
    
    def help_command(self, update, context):
        """Handle /help command."""
        help_msg = (
            "🤖 **Order Executor Bot Commands:**\n\n"
            "**Trading Commands:**\n"
            "• Send stock name/symbol to start trading\n"
            "• /trades - View all active trades\n"
            "• /m - Modify existing trades\n\n"
            "**Setup Commands:**\n"
            "• /start - Show welcome message\n"
            "• /reset - Reset preferences\n\n"
            "**Other Commands:**\n"
            "• /help - Show this help message\n\n"
            "💡 **How to trade:**\n"
            "1. Send stock name (e.g., 'Reliance' or 'RELIANCE')\n"
            "2. Select from search results\n"
            "3. Choose Market or Limit order\n"
            "4. Bot will place order and monitor SL/Target"
        )
        update.message.reply_text(help_msg, parse_mode='Markdown')
    
    def button_callback(self, update, context):
        """Handle button callbacks."""
        query = update.callback_query
        query.answer()
        
        if query.data == "view_trades":
            self._show_trades(query)
        elif query.data == "modify_trades":
            query.edit_message_text("🔧 Trade modification feature coming soon!")
        elif query.data == "help":
            self.help_command(update, context)
    
    def _show_trades(self, query):
        """Show active trades."""
        try:
            trades_with_pnl = self.trading_engine.get_active_trades_with_pnl()
            
            if not trades_with_pnl:
                query.edit_message_text("📊 No active trades found.")
                return
            
            trades_msg = "📊 **Active Trades:**\n\n"
            for i, trade in enumerate(trades_with_pnl, 1):
                symbol = trade.get('symbol', 'Unknown')
                qty = trade.get('qty', 0)
                entry_price = trade.get('entry_price', 0.0)
                current_price = trade.get('current_price', 0.0)
                pnl = trade.get('pnl', 0.0)
                pnl_pct = trade.get('pnl_percentage', 0.0)
                sl = trade.get('sl', 0.0)
                target = trade.get('tgt', 0.0)
                
                status_emoji = "🟢" if pnl >= 0 else "🔴"
                trades_msg += (
                    f"{i}. {status_emoji} **{symbol}**\n"
                    f"   Qty: {qty} | Entry: ₹{entry_price:.2f} | LTP: ₹{current_price:.2f}\n"
                    f"   SL: ₹{sl:.2f} | Target: ₹{target:.2f}\n"
                    f"   P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)\n\n"
                )
            
            query.edit_message_text(trades_msg, parse_mode='Markdown')
            
        except Exception as e:
            query.edit_message_text(f"❌ Error retrieving trades: {e}")
    
    def setup_handlers(self):
        """Setup message handlers."""
        # Conversation handler for trading flow
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start_command)],
            states={
                self.config.ASK_CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_capital)],
                self.config.ASK_SL: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_sl)],
                self.config.ASK_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_target)],
                self.config.READY: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_stock_input)],
            },
            fallbacks=[CommandHandler("reset", self.reset_command)],
        )
        
        self.app.add_handler(conv_handler)
        self.app.add_handler(CommandHandler("trades", self.trades_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    def handle_capital(self, update, context):
        """Handle capital input."""
        try:
            capital_text = update.message.text.strip()
            capital = float(capital_text.replace(',', ''))
            
            if capital <= 0:
                update.message.reply_text("❌ Capital must be greater than 0. Enter a valid amount.")
                return self.config.ASK_CAPITAL
            
            # Store capital in context
            context.user_data['capital'] = capital
            update.message.reply_text("📉 Enter Stoploss % (e.g., 0.2 or 0.2%)")
            return self.config.ASK_SL
            
        except ValueError:
            update.message.reply_text("❌ Invalid capital. Enter a valid number (e.g., 10000).")
            return self.config.ASK_CAPITAL
    
    def handle_sl(self, update, context):
        """Handle SL input."""
        try:
            sl_text = update.message.text.strip().replace('%', '')
            sl_percent = float(sl_text)
            
            if sl_percent <= 0 or sl_percent > 100:
                update.message.reply_text("❌ SL must be between 0 and 100%. Enter a valid percentage.")
                return self.config.ASK_SL
            
            # Store SL in context
            context.user_data['sl_percent'] = sl_percent
            update.message.reply_text("🎯 Enter Target % (e.g., 0.6 or 0.6%)")
            return self.config.ASK_TARGET
            
        except ValueError as e:
            update.message.reply_text(f"❌ Invalid SL: {e}")
            return self.config.ASK_SL
    
    def handle_target(self, update, context):
        """Handle target input."""
        try:
            target_text = update.message.text.strip().replace('%', '')
            target_percent = float(target_text)
            
            if target_percent <= 0 or target_percent > 100:
                update.message.reply_text("❌ Target must be between 0 and 100%. Enter a valid percentage.")
                return self.config.ASK_TARGET
            
            # Store target in context
            context.user_data['target_percent'] = target_percent
            
            # Save preferences
            self.config.save_preferences(
                context.user_data['capital'],
                context.user_data['sl_percent'],
                context.user_data['target_percent']
            )
            
            update.message.reply_text("✅ Setup complete! Now send me a stock name or symbol.")
            return self.config.READY
            
        except ValueError as e:
            update.message.reply_text(f"❌ Invalid Target: {e}")
            return self.config.ASK_TARGET
    
    def handle_stock_input(self, update, context):
        """Handle stock input."""
        stock_input = update.message.text.strip()
        update.message.reply_text(f"🔍 Searching for: {stock_input}")
        # For now, just acknowledge the input
        update.message.reply_text("📈 Stock search feature will be implemented soon!")
        return self.config.READY
    
    def trades_command(self, update, context):
        """Handle /trades command."""
        self._show_trades(update)
    
    def reset_command(self, update, context):
        """Handle /reset command."""
        self.config.clear_preferences()
        update.message.reply_text("🔄 Preferences reset. Use /start to begin setup.")
        return ConversationHandler.END
    
    def start_bot(self):
        """Start the telegram bot."""
        self.app = ApplicationBuilder().token(self.config.BOT_TOKEN).build()
        self.setup_handlers()
        print("🤖 Starting Telegram Bot...")
        self.app.run_polling()
