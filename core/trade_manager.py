class TradeManager:
    def __init__(self, kite_client, logger):
        self.logger = logger
        self.kite = kite_client
        self.journal = TradeJournal(logger)
        
        self.logger.info("Initializing Trade Manager")
        self.logger.debug(f"API Key: {kite_client.api_key[:5]}...")
        
    def place_order(self, order_details):
        """Enhanced with detailed logging"""
        try:
            self.logger.debug(f"Attempting order: {order_details}")
            
            # Actual order placement
            order_id = self.kite.place_order(**order_details)
            
            self.logger.info(
                f"Order {order_id} placed successfully | "
                f"Type: {order_details['transaction_type']} | "
                f"Symbol: {order_details['tradingsymbol']}"
            )
            
            # Journal entry
            self.journal.log_order({
                'order_id': order_id,
                **order_details
            })
            
            return order_id
            
        except Exception as e:
            self.logger.error(
                f"Order failed: {str(e)} | "
                f"Details: {order_details}"
            )
            self.journal.log_order({
                **order_details,
                'status': 'FAILED',
                'error': str(e)
            })
            raise

    def _handle_tick(self, tick):
        """Tick processing with logging"""
        self.logger.debug(f"Processing tick: {tick}")
        try:
            # Tick handling logic
            pass
        except Exception as e:
            self.logger.error(f"Tick processing failed: {str(e)}")
            self.logger.debug(f"Problematic tick: {tick}")
            raise

    def daily_summary(self):
        """End-of-day report"""
        positions = self.kite.positions()
        margin = self.kite.margins()
        
        self.logger.info(
            "End-of-Day Report\n"
            f"Total Positions: {len(positions['net'])}\n"
            f"Margin Used: {margin['equity']['used']:.2f}\n"
            f"Margin Available: {margin['equity']['available']:.2f}"
        )
        
        self.journal.log_snapshot({
            'active_orders': len(self.active_orders),
            'closed_orders': self.closed_orders_count,
            'realized_pnl': self.calculate_realized_pnl(),
            'unrealized_pnl': self.calculate_unrealized_pnl(),
            'margin_used': margin['equity']['used']
        })
