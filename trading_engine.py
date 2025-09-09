"""
Trading engine module for order management and trade logic.
Handles order placement, trade monitoring, and exit strategies.
"""

import asyncio
import csv
import json
import os
from datetime import datetime
from api_client import APIClient
from trade_logger import TradeLogger
from config import Config
from utils import format_pnl_message, calculate_pnl, is_market_open


class TradingEngine:
    """Main trading engine for order management and trade execution."""
    
    def __init__(self, config: Config, api_client: APIClient, trade_logger: TradeLogger):
        """Initialize trading engine with dependencies."""
        self.config = config
        self.api_client = api_client
        self.trade_logger = trade_logger
        self.active_trades = config.active_trades
        self.last_ltp = config.last_ltp
        self.persistence_file = "active_trades.json"
        
        # Load persisted trades on startup
        self.load_persisted_trades()
    
    def place_long_order(self, symbol, exchange, token, trade_amount, trade_sl, trade_target, context, order_type="MKT", limit_price=None):
        """Place a LONG order and register it for monitoring."""
        print(f"🚀 Placing LONG {order_type} order for: {symbol} ({exchange}:{token})")

        try:
            # Subscribe to symbol for real-time updates
            if not self.api_client.subscribe_symbol(exchange, token):
                return None, "❌ Failed to subscribe to symbol."

            # Get current quote for reference
            quote = self.api_client.get_quote(exchange, token)
            if not quote or "lp" not in quote:
                return None, "❌ LTP not available."

            last_price = float(quote["lp"])
            
            # Calculate quantity based on order type
            if order_type == "MKT":
                # For market orders, use current price
                price_for_qty = last_price
            else:
                # For limit orders, use limit price
                price_for_qty = limit_price
            
            quantity = int(trade_amount / price_for_qty)
            if quantity <= 0:
                return None, "⚠️ Quantity is 0."

            # Calculate SL and target prices based on entry price
            entry_price = limit_price if order_type == "LMT" else last_price
            sl_price = round(entry_price * (1 - trade_sl / 100), 2)
            tgt_price = round(entry_price * (1 + trade_target / 100), 2)

            # Place the order
            order_resp = self.api_client.place_order(
                buy_or_sell="B",
                product_type="I",  # Use "I" for Intraday like working code
                exchange=exchange,
                tradingsymbol=symbol,
                quantity=quantity,
                discloseqty=0,
                price_type=order_type,
                price=limit_price if order_type == "LMT" else 0.0,
                trigger_price=None,
                retention="DAY",
                remarks="TG-Bot-Order"
            )

            if order_resp and order_resp.get("stat") == "Ok":
                order_id = order_resp.get("norenordno")
                entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Store trade information with pending status
                self.active_trades[order_id] = {
                    "symbol": symbol,
                    "sl": sl_price,
                    "tgt": tgt_price,
                    "sl_percent": trade_sl,  # Store SL percentage for recalculation
                    "target_percent": trade_target,  # Store target percentage for recalculation
                    "exch": exchange,
                    "token": token,
                    "qty": quantity,
                    "entry_price": last_price,
                    "entry_time": entry_time,
                    "context": context,
                    "order_status": "PENDING",
                    "order_type": order_type,
                    "limit_price": limit_price if order_type == "LMT" else None
                }
                
                # Save trades to persistence file
                self.save_active_trades()

                # For market orders, assume immediate fill
                if order_type == "MKT":
                    # Log the trade entry immediately for market orders
                    row_index = self.trade_logger.log_trade_entry(symbol, last_price, entry_time)
                    if row_index is not None:
                        self.active_trades[order_id]["log_row"] = row_index
                    
                    # Update order status to complete
                    self.active_trades[order_id]["order_status"] = "COMPLETE"
                    
                    # Calculate PnL information
                    pnl_info = format_pnl_message(entry_price, sl_price, tgt_price, quantity)
                    
                    confirmation_msg = (
                        f"✅ Order Filled Successfully!\n\n"
                        f"📌 Symbol: {symbol}\n"
                        f"📋 Type: Market Order\n"
                        f"💰 Entry: {entry_price}\n"
                        f"📦 Qty: {quantity}\n"
                        f"📉 SL: {sl_price}\n"
                        f"🎯 Target: {tgt_price}\n"
                        f"🆔 Order No: {order_id}\n\n"
                        f"{pnl_info}"
                    )
                else:
                    # For limit orders, show placed status
                    order_type_display = f"Limit Order @ ₹{limit_price}"
                    
                    confirmation_msg = (
                        f"📋 Order Placed Successfully!\n\n"
                        f"📌 Symbol: {symbol}\n"
                        f"📋 Type: {order_type_display}\n"
                        f"💰 Limit Price: {limit_price}\n"
                        f"📦 Qty: {quantity}\n"
                        f"📉 SL: {sl_price}\n"
                        f"🎯 Target: {tgt_price}\n"
                        f"🆔 Order No: {order_id}\n\n"
                        f"⏳ Waiting for order to fill...\n"
                        f"📊 Current LTP: {last_price}"
                    )
                
                return order_resp, confirmation_msg
            else:
                # Enhanced error handling with specific error messages
                if not order_resp:
                    error_msg = "❌ Order Failed: No response from API. Check your internet connection."
                    return None, error_msg
                else:
                    error_code = order_resp.get('emsg', 'Unknown error')
                    
                    # Check if it's a margin-related rejection that we should bypass
                    if self._is_margin_related_error(error_code):
                        print(f"🔄 Margin-related rejection detected, treating as filled for testing: {error_code}")
                        return self._handle_margin_bypass(symbol, exchange, token, last_price, quantity, sl_price, tgt_price, context, order_type, limit_price, entry_time)
                    
                    # Handle other errors
                    error_msg = f"❌ Order Failed: {error_code}"
                    
                    # Add helpful suggestions based on common errors
                    if "market" in error_code.lower() or "closed" in error_code.lower():
                        error_msg += "\n\n💡 Market is closed. Trading hours: 9:15 AM - 3:30 PM IST"
                    elif "insufficient" in error_code.lower() or "fund" in error_code.lower():
                        error_msg += "\n\n💡 Insufficient funds. Check your account balance."
                    elif "invalid" in error_code.lower() or "symbol" in error_code.lower():
                        error_msg += "\n\n💡 Invalid symbol. Try searching again."
                    elif "product" in error_code.lower():
                        error_msg += "\n\n💡 Product type issue. Check MIS/CNC settings."
                    else:
                        error_msg += f"\n\n💡 Error details: {error_code}"
                
                return None, error_msg

        except Exception as e:
            return None, f"🚨 Order placement failed: {e}"

    def _is_margin_related_error(self, error_code):
        """Check if the error is margin-related and should be bypassed for testing."""
        if not error_code:
            return False
        
        error_lower = error_code.lower()
        margin_keywords = [
            "margin", "insufficient", "fund", "balance", "collateral", 
            "exposure", "limit", "risk", "leverage", "position"
        ]
        
        return any(keyword in error_lower for keyword in margin_keywords)

    def _handle_margin_bypass(self, symbol, exchange, token, last_price, quantity, sl_price, tgt_price, context, order_type, limit_price, entry_time):
        """Handle margin-related rejections by treating them as filled for testing purposes."""
        try:
            # Generate a mock order ID for testing
            mock_order_id = f"TEST_{int(datetime.now().timestamp())}"
            
            # Store trade information as if it was filled
            self.active_trades[mock_order_id] = {
                "symbol": symbol,
                "sl": sl_price,
                "tgt": tgt_price,
                "exch": exchange,
                "token": token,
                "qty": quantity,
                "entry_price": last_price,
                "entry_time": entry_time,
                "context": context,
                "order_status": "COMPLETE",
                "order_type": order_type,
                "limit_price": limit_price if order_type == "LMT" else None,
                "is_test_trade": True  # Mark as test trade
            }

            # Log the trade entry
            row_index = self.trade_logger.log_trade_entry(symbol, last_price, entry_time)
            if row_index is not None:
                self.active_trades[mock_order_id]["log_row"] = row_index
            
            # Calculate PnL information
            pnl_info = format_pnl_message(last_price, sl_price, tgt_price, quantity)
            
            confirmation_msg = (
                f"🔄 Order Bypassed (Margin Issue) - Treated as Filled for Testing\n\n"
                f"📌 Symbol: {symbol}\n"
                f"📋 Type: {order_type} Order\n"
                f"💰 Entry: {last_price}\n"
                f"📦 Qty: {quantity}\n"
                f"📉 SL: {sl_price}\n"
                f"🎯 Target: {tgt_price}\n"
                f"🆔 Test Order ID: {mock_order_id}\n"
                f"⚠️ Note: This is a test trade due to margin constraints\n\n"
                f"{pnl_info}"
            )
            
            # Send notification about the bypass
            asyncio.create_task(self._send_bypass_notification(context, symbol, mock_order_id, last_price))
            
            return {"stat": "Ok", "norenordno": mock_order_id}, confirmation_msg
            
        except Exception as e:
            return None, f"🚨 Margin bypass failed: {e}"

    async def _send_bypass_notification(self, context, symbol, order_id, price):
        """Send notification about margin bypass."""
        try:
            bypass_msg = (
                f"🔄 Margin Bypass Notification\n\n"
                f"📌 Symbol: {symbol}\n"
                f"💰 Price: {price}\n"
                f"🆔 Test Order: {order_id}\n"
                f"⚠️ Order was rejected due to margin constraints but treated as filled for testing.\n"
                f"📊 Trade is now being monitored for SL/Target."
            )
            await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=bypass_msg)
        except Exception as e:
            print(f"⚠️ Failed to send bypass notification: {e}")

    async def exit_trade(self, order_id, trade, exit_price, reason, context):
        """Exit trade when SL/Target hit."""
        try:
            is_test_trade = trade.get("is_test_trade", False)
            
            if is_test_trade:
                # For test trades, just simulate the exit without placing actual order
                print(f"🔄 Simulating exit for test trade: {order_id}")
                exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_price = trade.get("entry_price", 0.0)
                qty = trade.get("qty", 0)
                pnl = round((exit_price - entry_price) * qty, 2)

                # Update log with exit information
                self.trade_logger.update_trade_exit(order_id, self.active_trades, exit_price, exit_time, pnl)

                # Unsubscribe from symbol
                try:
                    self.api_client.unsubscribe_symbol(trade['exch'], trade['token'])
                except Exception as ue:
                    print(f"⚠️ Unsubscribe failed: {ue}")

                # Prepare notification message for test trade
                if reason == "SL HIT":
                    msg = (f"🚨 Stoploss HIT! (Test Trade)\n\n📌 {trade['symbol']}\n"
                           f"💰 Entry: {entry_price}\n📉 Exit: {exit_price}\n"
                           f"📦 Qty: {qty}\n💸 PnL ≈ {pnl}\n"
                           f"⚠️ Note: This was a simulated exit for testing")
                else:
                    msg = (f"🎯 Target HIT! (Test Trade)\n\n📌 {trade['symbol']}\n"
                           f"💰 Entry: {entry_price}\n📈 Exit: {exit_price}\n"
                           f"📦 Qty: {qty}\n💸 PnL ≈ {pnl}\n"
                           f"⚠️ Note: This was a simulated exit for testing")

                # Send notification to channel
                await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=msg)
            else:
                # For real trades, place actual exit order
                exit_order_resp = self.api_client.place_order(
                    buy_or_sell="S",
                    product_type="I",  # Use "I" for Intraday like working code
                    exchange=trade["exch"],
                    tradingsymbol=trade["symbol"],
                    quantity=trade["qty"],
                    discloseqty=0,
                    price_type="MKT",
                    price=0.0,
                    trigger_price=None,  # Added trigger_price parameter
                    retention="DAY",
                    remarks=f"Exit-{reason}"
                )

                if not exit_order_resp or exit_order_resp.get("stat") != "Ok":
                    error_msg = exit_order_resp.get('emsg', 'Unknown error') if exit_order_resp else 'No response'
                    print(f"❌ Exit order failed: {error_msg}")
                    
                    # Send failure notification
                    failure_msg = (
                        f"❌ Exit Order Failed!\n\n"
                        f"📌 Symbol: {trade['symbol']}\n"
                        f"🆔 Order ID: {order_id}\n"
                        f"📋 Reason: {reason}\n"
                        f"💰 Exit Price: {exit_price}\n"
                        f"❌ Error: {error_msg}\n\n"
                        f"⚠️ Please check your account and try manual exit."
                    )
                    await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=failure_msg)
                    return

                exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_price = trade.get("entry_price", 0.0)
                qty = trade.get("qty", 0)
                pnl = round((exit_price - entry_price) * qty, 2)

                # Update log with exit information
                self.trade_logger.update_trade_exit(order_id, self.active_trades, exit_price, exit_time, pnl)

                # Unsubscribe from symbol
                try:
                    self.api_client.unsubscribe_symbol(trade['exch'], trade['token'])
                except Exception as ue:
                    print(f"⚠️ Unsubscribe failed: {ue}")

                # Prepare notification message
                if reason == "SL HIT":
                    msg = (f"🚨 Stoploss HIT!\n\n📌 {trade['symbol']}\n"
                           f"💰 Entry: {entry_price}\n📉 Exit: {exit_price}\n"
                           f"📦 Qty: {qty}\n💸 PnL ≈ {pnl}")
                else:
                    msg = (f"🎯 Target HIT!\n\n📌 {trade['symbol']}\n"
                           f"💰 Entry: {entry_price}\n📈 Exit: {exit_price}\n"
                           f"📦 Qty: {qty}\n💸 PnL ≈ {pnl}")

                # Send notification to channel
                await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=msg)

        except Exception as e:
            print(f"🚨 Exit order failed: {e}")
            # Send error notification
            try:
                error_msg = (
                    f"🚨 Exit Trade Error!\n\n"
                    f"📌 Symbol: {trade['symbol']}\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"📋 Reason: {reason}\n"
                    f"💰 Exit Price: {exit_price}\n"
                    f"❌ Error: {str(e)}\n\n"
                    f"⚠️ Please check your account and try manual exit."
                )
                await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=error_msg)
            except Exception as notify_error:
                print(f"⚠️ Failed to send error notification: {notify_error}")

        # Cleanup - remove from active trades
        if order_id in self.active_trades:
            del self.active_trades[order_id]
            # Save updated trades
            self.save_active_trades()

    def _handle_exit_sync(self, order_id, trade, exit_price, reason):
        """Handle trade exit synchronously when no event loop is available."""
        try:
            is_test_trade = trade.get("is_test_trade", False)
            
            if is_test_trade:
                # For test trades, just simulate the exit without placing actual order
                print(f"🔄 Simulating exit for test trade: {order_id}")
                exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry_price = trade.get("entry_price", 0.0)
                qty = trade.get("qty", 0)
                pnl = round((exit_price - entry_price) * qty, 2)

                # Update log with exit information
                self.trade_logger.update_trade_exit(order_id, self.active_trades, exit_price, exit_time, pnl)
                
                # Remove from active trades
                if order_id in self.active_trades:
                    del self.active_trades[order_id]
                    self.save_active_trades()
                
                print(f"✅ Test trade exit simulated: {trade['symbol']} at {exit_price} (P&L: {pnl})")
                return
            
            # For real trades, place the actual exit order
            print(f"🎯 Executing {reason} for {trade['symbol']} at {exit_price}")
            
            # Get trade details
            symbol = trade.get("symbol", "")
            qty = trade.get("qty", 0)
            exch = trade.get("exch", "NSE")
            product_type = trade.get("product_type", "I")
            
            # Determine order side (opposite of entry)
            # If it was a BUY order, we need to SELL
            order_side = "S"  # Default to SELL
            
            # Place exit order
            try:
                order_result = self.api_client.place_order(
                    symbol=symbol,
                    qty=qty,
                    price=exit_price,
                    side=order_side,
                    product_type=product_type,
                    order_type="MKT",  # Market order for immediate execution
                    exch=exch
                )
                
                if order_result.get("stat") == "Ok":
                    exit_order_id = order_result.get("norenordno")
                    print(f"✅ Exit order placed successfully: {exit_order_id}")
                    
                    # Update trade log
                    exit_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    entry_price = trade.get("entry_price", 0.0)
                    pnl = round((exit_price - entry_price) * qty, 2)
                    
                    # Update log with exit information
                    self.trade_logger.update_trade_exit(order_id, self.active_trades, exit_price, exit_time, pnl)
                    
                    # Remove from active trades
                    if order_id in self.active_trades:
                        del self.active_trades[order_id]
                        self.save_active_trades()
                    
                    print(f"✅ Trade exited successfully: {symbol} at {exit_price} (P&L: {pnl})")
                    
                else:
                    print(f"❌ Failed to place exit order: {order_result.get('emsg', 'Unknown error')}")
                    
            except Exception as order_error:
                print(f"❌ Error placing exit order: {order_error}")
            
        except Exception as e:
            print(f"❌ Error in synchronous exit handling: {e}")

    def check_trade_conditions(self, symbol, token, price):
        """Check if any active trades should be exited based on current price."""
        for order_id, trade in list(self.active_trades.items()):
            # Skip if trade is already being processed
            if trade.get("processing_exit", False):
                continue
                
            if token and trade["token"] == token:
                try:
                    # Ensure all values are properly converted to float
                    price_float = float(price) if price is not None else 0.0
                    sl_float = float(trade["sl"]) if trade["sl"] is not None else 0.0
                    tgt_float = float(trade["tgt"]) if trade["tgt"] is not None else 0.0
                    qty, exch = trade["qty"], trade["exch"]

                    print(f"➡️ Active Trade: OrderID={order_id}, SL={sl_float}, Target={tgt_float}, Qty={qty}")
                    print(f"➡️ Comparing LTP={price_float} with SL={sl_float} and Target={tgt_float}")

                    if price_float <= sl_float:
                        print(f"🚨 SL HIT for {trade['symbol']} at {price_float}")
                        # Mark trade as being processed to prevent multiple executions
                        trade["processing_exit"] = True
                        self.save_active_trades()
                        # Handle exit synchronously
                        self._handle_exit_sync(order_id, trade, price_float, "SL HIT")
                        break

                    if price_float >= tgt_float:
                        print(f"🎯 TARGET HIT for {trade['symbol']} at {price_float}")
                        # Mark trade as being processed to prevent multiple executions
                        trade["processing_exit"] = True
                        self.save_active_trades()
                        # Handle exit synchronously
                        self._handle_exit_sync(order_id, trade, price_float, "TARGET HIT")
                        break
                        
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Error converting values to float for trade {order_id}: {e}")
                    print(f"   Price: {price} (type: {type(price)})")
                    print(f"   SL: {trade['sl']} (type: {type(trade['sl'])})")
                    print(f"   Target: {trade['tgt']} (type: {type(trade['tgt'])})")
                    continue

    def get_active_trades_info(self):
        """Get information about currently active trades."""
        if not self.active_trades:
            return "No active trades"
        
        info = "📊 Active Trades:\n\n"
        for order_id, trade in self.active_trades.items():
            info += f"🆔 {order_id}: {trade['symbol']} | Entry: {trade['entry_price']} | SL: {trade['sl']} | Target: {trade['tgt']}\n"
        
        return info

    def get_trade_statistics(self):
        """Get trading statistics."""
        total_pnl = self.trade_logger.get_total_pnl()
        active_count = self.trade_logger.get_active_trades_count(self.active_trades)
        
        return {
            "total_pnl": total_pnl,
            "active_trades": active_count,
            "total_trades": len(self.trade_logger.get_trade_history())
        }
    
    def get_active_trades_with_pnl(self):
        """Get active trades with current PnL calculations."""
        if not self.active_trades:
            return []
        
        trades_with_pnl = []
        for order_id, trade in self.active_trades.items():
            try:
                # Get current price
                quote = self.api_client.get_quote(trade["exch"], trade["token"])
                if quote and "lp" in quote:
                    current_price = float(quote["lp"])
                else:
                    # Use last known LTP if available
                    current_price = self.config.last_ltp.get(trade["token"], trade["entry_price"])
                
                # Calculate current PnL
                entry_price = trade["entry_price"]
                qty = trade["qty"]
                current_pnl, current_pnl_pct = calculate_pnl(entry_price, current_price, qty)
                
                trades_with_pnl.append({
                    "order_id": order_id,
                    "symbol": trade["symbol"],
                    "entry_price": entry_price,
                    "current_price": current_price,
                    "sl": trade["sl"],
                    "tgt": trade["tgt"],
                    "qty": qty,
                    "current_pnl": current_pnl,
                    "current_pnl_pct": current_pnl_pct,
                    "entry_time": trade["entry_time"]
                })
                
            except Exception as e:
                print(f"⚠️ Error calculating PnL for {trade['symbol']}: {e}")
                # Add trade without PnL calculation
                trades_with_pnl.append({
                    "order_id": order_id,
                    "symbol": trade["symbol"],
                    "entry_price": trade["entry_price"],
                    "current_price": "N/A",
                    "sl": trade["sl"],
                    "tgt": trade["tgt"],
                    "qty": trade["qty"],
                    "current_pnl": "N/A",
                    "current_pnl_pct": "N/A",
                    "entry_time": trade["entry_time"]
                })
        
        return trades_with_pnl
    
    def get_active_trades_list(self):
        """Get list of active trades for selection."""
        if not self.active_trades:
            return {}
        
        trades_list = {}
        for order_id, trade in self.active_trades.items():
            test_indicator = " (TEST)" if trade.get("is_test_trade", False) else ""
            status_indicator = ""
            
            # Add status indicator for pending orders
            if trade.get("order_status") == "PENDING":
                status_indicator = " (PENDING)"
            elif trade.get("order_status") == "COMPLETE":
                status_indicator = " (FILLED)"
            
            display_name = f"{trade['symbol']}{test_indicator}{status_indicator} | Entry: {trade['entry_price']} | SL: {trade['sl']} | Target: {trade['tgt']}"
            trades_list[display_name] = order_id
        
        return trades_list
    
    async def recover_orphaned_trade(self, symbol, entry_price, entry_time, sl_percent, target_percent, context):
        """Recover an orphaned trade that was logged but not tracked."""
        try:
            # Calculate SL and target prices
            sl_price = round(entry_price * (1 - sl_percent / 100), 2)
            tgt_price = round(entry_price * (1 + target_percent / 100), 2)
            
            # Generate recovery order ID
            recovery_order_id = f"RECOVER_{int(datetime.now().timestamp())}"
            
            # Find the symbol details
            # Try to search for the symbol to get exchange and token
            search_data = None
            for exchange in ["NSE", "BSE"]:
                search_data = self.api_client.search_symbol(exchange, symbol)
                if search_data and "values" in search_data and search_data["values"]:
                    break
            
            if not search_data or "values" not in search_data or not search_data["values"]:
                return False, f"❌ Could not find symbol details for {symbol}"
            
            # Get the first matching symbol
            symbol_data = search_data["values"][0]
            exchange = symbol_data["exch"]
            token = symbol_data["token"]
            
            # Subscribe to symbol for real-time updates
            if not self.api_client.subscribe_symbol(exchange, token):
                return False, f"❌ Failed to subscribe to {symbol}"
            
            # Calculate quantity (assuming 10000 capital for recovery)
            quantity = int(10000 / entry_price)
            if quantity <= 0:
                quantity = 1
            
            # Store trade information
            self.active_trades[recovery_order_id] = {
                "symbol": symbol,
                "sl": sl_price,
                "tgt": tgt_price,
                "exch": exchange,
                "token": token,
                "qty": quantity,
                "entry_price": entry_price,
                "entry_time": entry_time,
                "context": context,
                "order_status": "COMPLETE",
                "order_type": "RECOVERED",
                "is_recovered_trade": True
            }
            
            # Update the existing log entry
            rows = []
            with open(self.trade_logger.log_file, mode="r") as f:
                rows = list(csv.reader(f))
            
            # Find the matching row
            for i, row in enumerate(rows):
                if len(row) >= 3 and row[0] == symbol and row[1] == str(entry_price) and row[2] == entry_time:
                    self.active_trades[recovery_order_id]["log_row"] = i
                    break
            
            recovery_msg = (
                f"🔄 Trade Recovery Successful!\n\n"
                f"📌 Symbol: {symbol}\n"
                f"💰 Entry: {entry_price}\n"
                f"📦 Qty: {quantity}\n"
                f"📉 SL: {sl_price}\n"
                f"🎯 Target: {tgt_price}\n"
                f"🆔 Recovery ID: {recovery_order_id}\n"
                f"⚠️ Note: This trade is now being monitored for SL/Target"
            )
            
            return True, recovery_msg
            
        except Exception as e:
            return False, f"❌ Recovery failed: {e}"
    
    def update_trade_sl(self, order_id, new_sl_percent):
        """Update stoploss for a specific trade."""
        if order_id not in self.active_trades:
            return False, "Trade not found"
        
        try:
            trade = self.active_trades[order_id]
            entry_price = trade["entry_price"]
            new_sl_price = round(entry_price * (1 - new_sl_percent / 100), 2)
            
            # Update the trade
            trade["sl"] = new_sl_price
            
            # Save updated trades
            self.save_active_trades()
            
            return True, f"✅ SL updated to {new_sl_price} ({new_sl_percent}%)"
        except Exception as e:
            return False, f"❌ Failed to update SL: {e}"
    
    def update_trade_target(self, order_id, new_target_percent):
        """Update target for a specific trade."""
        if order_id not in self.active_trades:
            return False, "Trade not found"
        
        try:
            trade = self.active_trades[order_id]
            entry_price = trade["entry_price"]
            new_target_price = round(entry_price * (1 + new_target_percent / 100), 2)
            
            # Update the trade
            trade["tgt"] = new_target_price
            
            # Save updated trades
            self.save_active_trades()
            
            return True, f"✅ Target updated to {new_target_price} ({new_target_percent}%)"
        except Exception as e:
            return False, f"❌ Failed to update target: {e}"
    
    async def manual_exit_trade(self, order_id, context):
        """Manually exit a trade."""
        if order_id not in self.active_trades:
            return False, "Trade not found"
        
        try:
            trade = self.active_trades[order_id]
            
            # Get current price
            quote = self.api_client.get_quote(trade["exch"], trade["token"])
            if not quote or "lp" not in quote:
                return False, "❌ Unable to get current price"
            
            current_price = float(quote["lp"])
            
            # Exit the trade
            await self.exit_trade(order_id, trade, current_price, "MANUAL EXIT", context)
            
            return True, f"✅ Trade manually exited at {current_price}"
        except Exception as e:
            return False, f"❌ Failed to exit trade: {e}"
    
    async def cancel_order(self, order_id, context):
        """Cancel a pending order."""
        if order_id not in self.active_trades:
            return False, "Order not found"
        
        try:
            trade = self.active_trades[order_id]
            
            # Check if order is pending
            if trade.get("order_status") != "PENDING":
                return False, f"❌ Order is not pending (Status: {trade.get('order_status')})"
            
            # Cancel the order via API
            cancel_resp = self.api_client.cancel_order(order_id)
            
            if cancel_resp and cancel_resp.get("stat") == "Ok":
                # Remove from active trades
                del self.active_trades[order_id]
                
                # Save updated trades
                self.save_active_trades()
                
                # Send cancellation notification
                cancel_msg = (
                    f"❌ Order Cancelled Successfully!\n\n"
                    f"📌 Symbol: {trade['symbol']}\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"💰 Limit Price: {trade.get('limit_price', 'N/A')}\n"
                    f"📦 Quantity: {trade['qty']}\n\n"
                    f"✅ Order has been cancelled and removed from monitoring."
                )
                await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=cancel_msg)
                
                return True, f"✅ Order {order_id} cancelled successfully"
            else:
                error_msg = cancel_resp.get('emsg', 'Unknown error') if cancel_resp else 'No response'
                return False, f"❌ Failed to cancel order: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Failed to cancel order: {e}"
    
    async def modify_limit_price(self, order_id, new_limit_price, context):
        """Modify the limit price of a pending order."""
        if order_id not in self.active_trades:
            return False, "Order not found"
        
        try:
            trade = self.active_trades[order_id]
            
            # Check if order is pending
            if trade.get("order_status") != "PENDING":
                return False, f"❌ Order is not pending (Status: {trade.get('order_status')})"
            
            # Modify the order via API
            modify_resp = self.api_client.modify_order(
                order_id=order_id,
                new_price=new_limit_price,
                new_quantity=trade['qty']
            )
            
            if modify_resp and modify_resp.get("stat") == "Ok":
                # Update the trade with new limit price
                old_price = trade.get('limit_price')
                trade['limit_price'] = new_limit_price
                
                # Recalculate SL and target based on new limit price
                sl_percent = trade.get('sl_percent', 0.2)
                target_percent = trade.get('target_percent', 0.6)
                sl_price = round(new_limit_price * (1 - sl_percent / 100), 2)
                tgt_price = round(new_limit_price * (1 + target_percent / 100), 2)
                
                trade['sl'] = sl_price
                trade['tgt'] = tgt_price
                
                # Send modification notification
                modify_msg = (
                    f"✅ Limit Price Modified Successfully!\n\n"
                    f"📌 Symbol: {trade['symbol']}\n"
                    f"🆔 Order ID: {order_id}\n"
                    f"💰 Old Price: ₹{old_price}\n"
                    f"💰 New Price: ₹{new_limit_price}\n"
                    f"📦 Quantity: {trade['qty']}\n"
                    f"📉 New SL: ₹{sl_price}\n"
                    f"🎯 New Target: ₹{tgt_price}\n\n"
                    f"⏳ Order is still pending with new limit price."
                )
                await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=modify_msg)
                
                return True, f"✅ Limit price updated to ₹{new_limit_price}"
            else:
                error_msg = modify_resp.get('emsg', 'Unknown error') if modify_resp else 'No response'
                return False, f"❌ Failed to modify order: {error_msg}"
                
        except Exception as e:
            return False, f"❌ Failed to modify order: {e}"
    
    async def handle_order_fill(self, order_id, fill_price, context):
        """Handle order fill notification from websocket."""
        if order_id not in self.active_trades:
            return
        
        trade = self.active_trades[order_id]
        
        # Update order status
        trade["order_status"] = "COMPLETE"
        trade["entry_price"] = fill_price  # Update with actual fill price
        
        # Log the trade entry with actual fill price
        row_index = self.trade_logger.log_trade_entry(trade["symbol"], fill_price, trade["entry_time"])
        if row_index is not None:
            trade["log_row"] = row_index
        
        # Calculate PnL information with actual fill price
        pnl_info = format_pnl_message(fill_price, trade["sl"], trade["tgt"], trade["qty"])
        
        # Send fill notification
        fill_msg = (
            f"✅ Order Filled Successfully!\n\n"
            f"📌 Symbol: {trade['symbol']}\n"
            f"📋 Type: {trade['order_type']}\n"
            f"💰 Fill Price: {fill_price}\n"
            f"📦 Qty: {trade['qty']}\n"
            f"📉 SL: {trade['sl']}\n"
            f"🎯 Target: {trade['tgt']}\n"
            f"🆔 Order No: {order_id}\n\n"
            f"{pnl_info}"
        )
        
        await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=fill_msg)
    
    async def handle_order_rejection(self, order_id, reason, context):
        """Handle order rejection notification."""
        if order_id not in self.active_trades:
            return
        
        trade = self.active_trades[order_id]
        
        # Update order status
        trade["order_status"] = "REJECTED"
        
        # Send rejection notification
        rejection_msg = (
            f"❌ Order Rejected!\n\n"
            f"📌 Symbol: {trade['symbol']}\n"
            f"🆔 Order No: {order_id}\n"
            f"📋 Reason: {reason}\n\n"
            f"Please try again with different parameters."
        )
        
        await context.bot.send_message(chat_id=self.config.TELEGRAM_CHANNEL_ID, text=rejection_msg)
        
        # Remove from active trades
        del self.active_trades[order_id]
    
    def save_active_trades(self):
        """Save active trades to JSON file for persistence."""
        try:
            # Create a serializable version of active trades (remove context)
            serializable_trades = {}
            for order_id, trade in self.active_trades.items():
                serializable_trade = trade.copy()
                # Remove non-serializable context
                if 'context' in serializable_trade:
                    del serializable_trade['context']
                serializable_trades[order_id] = serializable_trade
            
            with open(self.persistence_file, 'w') as f:
                json.dump(serializable_trades, f, indent=2)
            
            print(f"💾 Saved {len(serializable_trades)} active trades to {self.persistence_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving active trades: {e}")
            return False
    
    def load_persisted_trades(self):
        """Load persisted trades from JSON file."""
        try:
            if not os.path.exists(self.persistence_file):
                print("📁 No persisted trades file found, starting fresh")
                return
            
            with open(self.persistence_file, 'r') as f:
                persisted_trades = json.load(f)
            
            if not persisted_trades:
                print("📁 No persisted trades found")
                return
            
            print(f"🔄 Loading {len(persisted_trades)} persisted trades...")
            
            # Validate and load trades
            valid_trades = 0
            for order_id, trade_data in persisted_trades.items():
                if self._validate_persisted_trade(trade_data):
                    # Add to active trades (context will be None initially)
                    trade_data['context'] = None
                    self.active_trades[order_id] = trade_data
                    valid_trades += 1
                    print(f"✅ Restored trade: {trade_data['symbol']} (Order: {order_id})")
                else:
                    print(f"⚠️ Skipped invalid trade: {order_id}")
            
            print(f"✅ Successfully restored {valid_trades} valid trades")
            
        except Exception as e:
            print(f"❌ Error loading persisted trades: {e}")
    
    def _validate_persisted_trade(self, trade_data):
        """Validate a persisted trade before restoring it."""
        required_fields = ['symbol', 'sl', 'tgt', 'exch', 'token', 'qty', 'entry_price', 'entry_time']
        
        # Check required fields
        for field in required_fields:
            if field not in trade_data:
                print(f"⚠️ Missing required field '{field}' in trade data")
                return False
        
        # Check if trade is not too old (e.g., older than 1 day)
        try:
            entry_time = datetime.strptime(trade_data['entry_time'], "%Y-%m-%d %H:%M:%S")
            time_diff = datetime.now() - entry_time
            if time_diff.days > 1:
                print(f"⚠️ Trade too old: {trade_data['symbol']} from {trade_data['entry_time']}")
                return False
        except ValueError:
            print(f"⚠️ Invalid entry time format: {trade_data['entry_time']}")
            return False
        
        # Check if it's a test trade that should be cleaned up
        if trade_data.get('is_test_trade', False):
            print(f"⚠️ Skipping test trade: {trade_data['symbol']}")
            return False
        
        return True
    
    def cleanup_persisted_trades(self):
        """Clean up the persisted trades file."""
        try:
            if os.path.exists(self.persistence_file):
                os.remove(self.persistence_file)
                print(f"🗑️ Cleaned up persisted trades file")
        except Exception as e:
            print(f"❌ Error cleaning up persisted trades: {e}")
    
    def update_trade_context(self, order_id, context):
        """Update the context for a specific trade (used after Telegram bot restart)."""
        if order_id in self.active_trades:
            self.active_trades[order_id]['context'] = context
            print(f"🔄 Updated context for trade {order_id}")
    
    def get_trades_needing_context(self):
        """Get trades that need context updates (for Telegram bot restart)."""
        return [order_id for order_id, trade in self.active_trades.items() if trade.get('context') is None]
    
    def resubscribe_to_active_trades(self):
        """Resubscribe to websocket for all active trades."""
        try:
            subscribed_count = 0
            failed_count = 0
            
            for order_id, trade in self.active_trades.items():
                try:
                    if 'exch' in trade and 'token' in trade:
                        success = self.api_client.subscribe_symbol(trade['exch'], trade['token'])
                        if success:
                            subscribed_count += 1
                            print(f"✅ Resubscribed to {trade['symbol']} ({trade['exch']}:{trade['token']})")
                        else:
                            failed_count += 1
                            print(f"❌ Failed to resubscribe to {trade['symbol']}")
                except Exception as e:
                    failed_count += 1
                    print(f"❌ Error resubscribing to {trade.get('symbol', 'Unknown')}: {e}")
            
            print(f"📡 Websocket Resubscription: {subscribed_count} successful, {failed_count} failed")
            return subscribed_count, failed_count
            
        except Exception as e:
            print(f"❌ Error in resubscribe_to_active_trades: {e}")
            return 0, 0
