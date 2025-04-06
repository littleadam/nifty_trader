import time
from datetime import datetime, timedelta

class TradingSafeguards:
    def __init__(self, kite_client):
        self.kite = kite_client
        self.last_order_time = None
        self.order_count = 0
        
    def check_market_hours(self):
        """Ensure trading is only during market hours"""
        now = datetime.now().time()
        market_open = datetime.strptime('09:15', '%H:%M').time()
        market_close = datetime.strptime('15:30', '%H:%M').time()
        
        if not (market_open <= now <= market_close):
            raise Exception("Trading outside market hours")
            
    def enforce_rate_limit(self):
        """Limit to 30 orders per minute"""
        if self.last_order_time and (time.time() - self.last_order_time < 2):
            time.sleep(2 - (time.time() - self.last_order_time))
            
        if self.order_count >= 30:
            current_minute = datetime.now().minute
            while datetime.now().minute == current_minute:
                time.sleep(1)
            self.order_count = 0
            
    def validate_liquidity(self, symbol, quantity):
        """Check order book depth before trading"""
        depth = self.kite.quote(symbol)['depth']
        best_5_volume = sum(item['quantity'] for item in depth['sell'][:5])
        
        if best_5_volume < quantity * 3:
            raise Exception(f"Insufficient liquidity for {quantity} lots in {symbol}")
            
    def check_corporate_action(self, symbol):
        """Verify no corporate action is pending"""
        instruments = self.kite.instruments('NFO')
        instrument = next((i for i in instruments if i['tradingsymbol'] == symbol), None)
        
        if instrument and instrument['lot_size'] != TRADE_CONFIG['lot_size']:
            raise Exception("Corporate action detected - lot size changed")
            
    def pre_trade_checks(self, symbol, quantity):
        """Run all validations before order placement"""
        self.check_market_hours()
        self.enforce_rate_limit()
        self.validate_liquidity(symbol, quantity)
        self.check_corporate_action(symbol)
