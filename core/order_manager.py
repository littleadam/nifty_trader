class OrderManager:
    def __init__(self, kite_client, safeguards):
        self.kite = kite_client
        self.safeguards = safeguards
        self.pending_orders = {}

    def place_sell_order(self, symbol, quantity):
        """Complete sell order with all validations"""
        try:
            self.safeguards.pre_trade_checks(symbol, quantity)
            
            # Get instrument token
            instruments = self.kite.instruments('NFO')
            instrument = next((i for i in instruments if i['tradingsymbol'] == symbol), None)
            if not instrument:
                raise Exception(f"Instrument {symbol} not found")
            
            # Check lot size
            if quantity % instrument['lot_size'] != 0:
                raise Exception(f"Quantity {quantity} not multiple of lot size {instrument['lot_size']}")
            
            # Place order
            ltp = self.kite.ltp(f"NFO:{symbol}")[f"NFO:{symbol}"]['last_price']
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange="NFO",
                tradingsymbol=symbol,
                transaction_type="SELL",
                quantity=quantity,
                product=TRADE_CONFIG['product_type'],
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=round(ltp * 0.95, 1),  # 5% below LTP
                validity="DAY"
            )
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'quantity': quantity,
                'timestamp': datetime.now()
            }
            
            print(f"Sell order placed: {order_id} for {symbol}")
            return order_id
            
        except Exception as e:
            print(f"Sell order failed: {str(e)}")
            self.safeguards.record_error()
            return None

    def place_sl_order(self, symbol, quantity, trigger_price):
        """Complete SL order with price validation"""
        try:
            self.safeguards.pre_trade_checks(symbol, quantity)
            
            ltp = self.kite.ltp(f"NFO:{symbol}")[f"NFO:{symbol}"]['last_price']
            if trigger_price > ltp * 1.1:  # Prevent unrealistic triggers
                raise Exception("Trigger price too far from LTP")
            
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_STOPLOSS,
                exchange="NFO",
                tradingsymbol=symbol,
                transaction_type="BUY",
                quantity=quantity,
                product=TRADE_CONFIG['product_type'],
                order_type=self.kite.ORDER_TYPE_SL,
                price=round(trigger_price * 0.98, 1),  # 2% below trigger
                trigger_price=round(trigger_price, 1),
                validity="DAY"
            )
            
            self.pending_orders[order_id] = {
                'symbol': symbol,
                'quantity': quantity,
                'is_sl': True,
                'timestamp': datetime.now()
            }
            
            print(f"SL order placed: {order_id} for {symbol}")
            return order_id
            
        except Exception as e:
            print(f"SL order failed: {str(e)}")
            self.safeguards.record_error()
            return None

    def cancel_stale_orders(self, timeout_minutes=30):
        """Cancel orders pending too long"""
        now = datetime.now()
        cancelled = 0
        
        for order_id, details in list(self.pending_orders.items()):
            if (now - details['timestamp']).total_seconds() > timeout_minutes * 60:
                try:
                    self.kite.cancel_order(
                        variety=self.kite.VARIETY_REGULAR,
                        order_id=order_id
                    )
                    del self.pending_orders[order_id]
                    cancelled += 1
                    print(f"Cancelled stale order: {order_id}")
                except Exception as e:
                    print(f"Failed to cancel order {order_id}: {str(e)}")
        
        return cancelled
