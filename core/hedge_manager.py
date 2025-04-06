class HedgeManager:
    def __init__(self, kite_client, position_tracker):
        self.kite = kite_client
        self.tracker = position_tracker
        self.expiry_manager = ExpiryManager()

    def _get_avg_sell_premium(self, expiry, option_type):
        """Calculate average premium from executed sell orders"""
        total_premium = 0
        total_quantity = 0
        
        orders = self.kite.orders()
        for order in orders:
            if (order['status'] == 'COMPLETE' and 
                order['transaction_type'] == 'SELL' and
                order['product'] == 'OPT'):
                
                history = self.kite.order_history(order['order_id'])
                last_exec = history[-1]
                
                if (expiry in last_exec['tradingsymbol']) and \
                   (option_type in last_exec['tradingsymbol']):
                    total_premium += last_exec['average_price'] * last_exec['filled_quantity']
                    total_quantity += last_exec['filled_quantity']
        
        return total_premium / total_quantity if total_quantity > 0 else 0

    def _get_sell_strike(self, expiry, option_type):
        """Get strike price from existing sell positions"""
        positions = self.kite.positions()['net']
        for p in positions:
            if (p['expiry'] == expiry and 
                option_type in p['tradingsymbol'] and 
                p['quantity'] < 0):
                return int(p['tradingsymbol'].split(option_type)[0][-5:])
        return 0

    def _generate_symbol(self, option_type, strike, expiry_date):
        """Generate NFO symbol string"""
        expiry_str = expiry_date.strftime('%d%b%y').upper()
        return f"NIFTY{expiry_str}{strike}{option_type}"

    def _calculate_required_hedge(self, expiry, option_type):
        """Enhanced with proper quantity calculation"""
        sell_qty = self.tracker.positions[expiry][option_type]['sell']['qty']
        buy_qty = self.tracker.positions[expiry][option_type]['buy']['qty']
        return max(0, sell_qty - buy_qty)

    def _place_hedge_order(self, expiry, option_type, quantity):
        """Complete order placement with validation"""
        if quantity <= 0:
            return None

        strike = self._calculate_hedge_strike(expiry, option_type)
        weekly_expiry = self.expiry_manager.get_next_weekly_expiry()
        symbol = self._generate_symbol(option_type, strike, weekly_expiry)
        
        try:
            ltp_data = self.kite.ltp(f"NFO:{symbol}")
            ltp = ltp_data[f"NFO:{symbol}"]['last_price']
            
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange="NFO",
                tradingsymbol=symbol,
                transaction_type="BUY",
                quantity=quantity,
                product=TRADE_CONFIG['product_type'],
                order_type=self.kite.ORDER_TYPE_LIMIT,
                price=round(ltp * 1.05, 1)  # 5% above LTP
            )
            print(f"Hedge order placed: {order_id} for {symbol}")
            return order_id
        except Exception as e:
            print(f"Failed to place hedge: {str(e)}")
            return None
