"""
Trading engine module for order management and trade logic.
Handles order placement, trade monitoring, and exit strategies.
"""

import asyncio
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

                # Store trade information
                self.active_trades[order_id] = {
                    "symbol": symbol,
                    "sl": sl_price,
                    "tgt": tgt_price,
                    "exch": exchange,
                    "token": token,
                    "qty": quantity,
                    "entry_price": last_price,
                    "entry_time": entry_time,
                    "context": context
                }

                # Log the trade entry
                row_index = self.trade_logger.log_trade_entry(symbol, last_price, entry_time)
                if row_index is not None:
                    self.active_trades[order_id]["log_row"] = row_index

                # Calculate PnL information
                pnl_info = format_pnl_message(entry_price, sl_price, tgt_price, quantity)
                
                order_type_display = "Market Order" if order_type == "MKT" else f"Limit Order @ ₹{limit_price}"
                
                confirmation_msg = (
                    f"✅ Order Placed Successfully!\n\n"
                    f"📌 Symbol: {symbol}\n"
                    f"📋 Type: {order_type_display}\n"
                    f"💰 Entry: {entry_price}\n"
                    f"📦 Qty: {quantity}\n"
                    f"📉 SL: {sl_price}\n"
                    f"🎯 Target: {tgt_price}\n"
                    f"🆔 Order No: {order_id}\n\n"
                    f"{pnl_info}"
                )
                return order_resp, confirmation_msg
            else:
                # Enhanced error handling with specific error messages
                if not order_resp:
                    error_msg = "❌ Order Failed: No response from API. Check your internet connection."
                else:
                    error_code = order_resp.get('emsg', 'Unknown error')
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
                
                return None, error_msg

        except Exception as e:
            return None, f"🚨 Order placement failed: {e}"

    async def exit_trade(self, order_id, trade, exit_price, reason, context):
        """Exit trade when SL/Target hit."""
        try:
            # Place exit order
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
                print(f"❌ Exit order failed: {exit_order_resp.get('emsg', 'Unknown error') if exit_order_resp else 'No response'}")
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

            # Send notification
            await context.bot.send_message(chat_id=context._chat_id, text=msg)

        except Exception as e:
            print(f"🚨 Exit order failed: {e}")

        # Cleanup - remove from active trades
        if order_id in self.active_trades:
            del self.active_trades[order_id]

    def check_trade_conditions(self, symbol, token, price):
        """Check if any active trades should be exited based on current price."""
        for order_id, trade in list(self.active_trades.items()):
            if token and trade["token"] == token:
                sl, tgt = trade["sl"], trade["tgt"]
                qty, exch = trade["qty"], trade["exch"]

                print(f"➡️ Active Trade: OrderID={order_id}, SL={sl}, Target={tgt}, Qty={qty}")
                print(f"➡️ Comparing LTP={price} with SL={sl} and Target={tgt}")

                if price <= sl:
                    print(f"🚨 SL HIT for {trade['symbol']} at {price}")
                    context = trade["context"]
                    asyncio.create_task(self.exit_trade(order_id, trade, price, "SL HIT", context))
                    break

                if price >= tgt:
                    print(f"🎯 TARGET HIT for {trade['symbol']} at {price}")
                    context = trade["context"]
                    asyncio.create_task(self.exit_trade(order_id, trade, price, "TARGET HIT", context))
                    break

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
            display_name = f"{trade['symbol']} | Entry: {trade['entry_price']} | SL: {trade['sl']} | Target: {trade['tgt']}"
            trades_list[display_name] = order_id
        
        return trades_list
    
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
