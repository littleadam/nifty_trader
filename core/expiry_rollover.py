class ExpiryRollover:
    def __init__(self, kite_client, position_tracker):
        self.kite = kite_client
        self.tracker = position_tracker
        
    def rollover_expiring_positions(self):
        """Replace expiring hedges with new weekly positions"""
        for expiry in self._get_expiring_hedges():
            for option_type in ['CE', 'PE']:
                quantity = self.tracker.positions[expiry][option_type]['buy']
                if quantity > 0:
                    self._rollover_single_hedge(expiry, option_type, quantity)
                    
    def _rollover_single_hedge(self, old_expiry, option_type, quantity):
        """Replace one expiring hedge"""
        old_strike = self._get_hedge_strike(old_expiry, option_type)
        new_strike = self._calculate_rollover_strike(old_strike, option_type)
        new_expiry = ExpiryManager().get_next_weekly_expiry()
        
        # Place new hedge
        new_symbol = self._generate_symbol(option_type, new_strike, new_expiry)
        self.kite.place_order(
            variety=self.kite.VARIETY_REGULAR,
            exchange=TRADE_CONFIG['exchange'],
            tradingsymbol=new_symbol,
            transaction_type="BUY",
            quantity=quantity,
            product=TRADE_CONFIG['product_type'],
            order_type=self.kite.ORDER_TYPE_LIMIT,
            price=self.kite.ltp(new_symbol)[new_symbol]['last_price'] * 1.05
        )
        
        # Cancel old hedge
        old_symbol = self._generate_symbol(option_type, old_strike, old_expiry)
        orders = self.kite.orders()
        for order in orders:
            if order['tradingsymbol'] == old_symbol and order['status'] == 'OPEN':
                self.kite.cancel_order(
                    variety=order['variety'],
                    order_id=order['order_id']
                )
