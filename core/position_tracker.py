from collections import defaultdict
from datetime import datetime

class PositionTracker:
    def __init__(self, kite_client):
        self.kite = kite_client
        self.positions = defaultdict(lambda: {'CE': {'sell': {'qty': 0, 'avg_price': 0},
                                              'buy': {'qty': 0, 'avg_price': 0}},
                                    'PE': {'sell': {'qty': 0, 'avg_price': 0},
                                           'buy': {'qty': 0, 'avg_price': 0}})
        self.order_history_cache = {}

    def refresh_positions(self):
        """Sync with broker positions and calculate averages"""
        positions = self.kite.positions()['net']
        orders = self.kite.orders()
        
        # Clear existing data
        self.positions.clear()
        self._cache_order_history(orders)
        
        # Process current positions
        for p in positions:
            if p['product'] == 'OPT':
                expiry = p['expiry']
                option_type = 'CE' if 'CE' in p['tradingsymbol'] else 'PE'
                direction = 'sell' if p['quantity'] < 0 else 'buy'
                
                self.positions[expiry][option_type][direction]['qty'] = abs(p['quantity'])
                self.positions[expiry][option_type][direction]['avg_price'] = p['average_price']

    def _cache_order_history(self, orders):
        """Cache order history for premium calculation"""
        self.order_history_cache = {}
        for order in orders:
            if order['status'] == 'COMPLETE' and order['product'] == 'OPT':
                history = self.kite.order_history(order['order_id'])
                self.order_history_cache[order['order_id']] = history[-1]  # Last execution

    def _get_avg_sell_price(self, expiry, option_type):
        """Calculate average sell price from executed orders"""
        total_value = 0
        total_quantity = 0
        
        for order_id, execution in self.order_history_cache.items():
            if (execution['tradingsymbol'].endswith(option_type) and \
               (expiry in execution['tradingsymbol']) and \
               (execution['transaction_type'] == 'SELL'):
                total_value += execution['average_price'] * execution['filled_quantity']
                total_quantity += execution['filled_quantity']
        
        return total_value / total_quantity if total_quantity > 0 else 0

    def _get_ltp(self, expiry, option_type):
        """Get last traded price for given option"""
        instruments = self.kite.instruments('NFO')
        symbol = next((i['tradingsymbol'] for i in instruments 
                     if i['expiry'] == expiry and 
                     i['instrument_type'] == option_type), None)
        
        if symbol:
            return self.kite.ltp(f"NFO:{symbol}")[f"NFO:{symbol}"]['last_price']
        return 0

    def _get_strike(self, expiry, option_type):
        """Extract strike price from symbol"""
        positions = self.kite.positions()['net']
        for p in positions:
            if p['expiry'] == expiry and option_type in p['tradingsymbol']:
                return int(p['tradingsymbol'].split(option_type)[0][-5:])
        return 0

    def get_profitable_legs(self, profit_threshold):
        """Enhanced with proper average price calculation"""
        profitable = []
        self.refresh_positions()
        
        for expiry in list(self.positions.keys()):
            for option_type in ['CE', 'PE']:
                sell_data = self.positions[expiry][option_type]['sell']
                if sell_data['qty'] > 0:
                    avg_price = sell_data['avg_price']
                    ltp = self._get_ltp(expiry, option_type)
                    
                    if ltp > 0 and avg_price > 0:
                        profit_pct = (avg_price - ltp) / avg_price
                        if profit_pct >= profit_threshold:
                            profitable.append({
                                'expiry': expiry,
                                'type': option_type,
                                'strike': self._get_strike(expiry, option_type),
                                'quantity': sell_data['qty'],
                                'avg_price': avg_price,
                                'symbol': self._get_symbol(expiry, option_type)
                            })
        return profitable

    def _get_symbol(self, expiry, option_type):
        """Generate symbol from existing positions"""
        positions = self.kite.positions()['net']
        for p in positions:
            if p['expiry'] == expiry and option_type in p['tradingsymbol']:
                return p['tradingsymbol']
        return None
