import csv
from datetime import datetime

class TradeJournal:
    def __init__(self, logger):
        self.logger = logger
        self.journal_file = "logs/trade_journal.csv"
        self._init_journal_file()
        
    def _init_journal_file(self):
        """Initialize CSV file with headers"""
        try:
            with open(self.journal_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow([
                        'timestamp', 'order_id', 'symbol', 'type', 
                        'quantity', 'price', 'status', 'premium',
                        'underlying_price', 'vix', 'error'
                    ])
                    self.logger.info("Created new trade journal file")
        except Exception as e:
            self.logger.error(f"Journal init failed: {str(e)}")
            raise

    def log_order(self, order_data):
        """Log order details to CSV and logger"""
        try:
            with open(self.journal_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().isoformat(),
                    order_data.get('order_id', 'N/A'),
                    order_data.get('symbol', 'N/A'),
                    order_data.get('type', 'N/A'),
                    order_data.get('quantity', 0),
                    order_data.get('price', 0.0),
                    order_data.get('status', 'PENDING'),
                    order_data.get('premium', 0.0),
                    order_data.get('underlying', 0.0),
                    order_data.get('vix', 0.0),
                    order_data.get('error', '')
                ])
            
            self.logger.info(
                f"Order {order_data.get('order_id', 'N/A')} logged | "
                f"Symbol: {order_data.get('symbol', 'N/A')} | "
                f"Type: {order_data.get('type', 'N/A')} | "
                f"Qty: {order_data.get('quantity', 0)}"
            )
            
        except Exception as e:
            self.logger.error(f"Order logging failed: {str(e)}")
            raise

    def log_snapshot(self, snapshot_data):
        """Log system snapshot to separate CSV"""
        try:
            with open("logs/system_snapshot.csv", 'a', newline='') as f:
                writer = csv.writer(f)
                if f.tell() == 0:
                    writer.writerow([
                        'timestamp', 'active_orders', 'closed_orders',
                        'realized_pnl', 'unrealized_pnl', 'margin_used'
                    ])
                    
                writer.writerow([
                    datetime.now().isoformat(),
                    snapshot_data.get('active_orders', 0),
                    snapshot_data.get('closed_orders', 0),
                    snapshot_data.get('realized_pnl', 0.0),
                    snapshot_data.get('unrealized_pnl', 0.0),
                    snapshot_data.get('margin_used', 0.0)
                ])
            
            self.logger.info(
                f"System Snapshot | "
                f"Active: {snapshot_data.get('active_orders', 0)} | "
                f"Closed: {snapshot_data.get('closed_orders', 0)} | "
                f"Realized P&L: {snapshot_data.get('realized_pnl', 0.0):.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Snapshot logging failed: {str(e)}")
            raise
