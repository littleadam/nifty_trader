#!/usr/bin/env python3
import logging
from config.settings import API_CREDENTIALS, TRADE_CONFIG
from utils.logger import configure_logger
from core.trade_manager import TradeManager
from core.position_tracker import PositionTracker
from core.hedge_manager import HedgeManager
from core.order_manager import OrderManager
from core.safeguards import TradingSafeguards
from core.trade_journal import TradeJournal
from kiteconnect import KiteConnect

def initialize_components():
    """Initialize all system components with dependency injection"""
    logger = configure_logger('main')
    
    try:
        # Initialize Kite Connect
        kite = KiteConnect(api_key=API_CREDENTIALS['api_key'])
        kite.set_access_token(API_CREDENTIALS['access_token'])
        logger.info("Kite Connect initialized successfully")

        # Core components
        safeguards = TradingSafeguards(kite)
        journal = TradeJournal(logger)
        position_tracker = PositionTracker(kite)
        hedge_manager = HedgeManager(kite, position_tracker)
        order_manager = OrderManager(kite, safeguards, journal)
        
        # Main trading manager
        trade_manager = TradeManager(
            kite=kite,
            position_tracker=position_tracker,
            hedge_manager=hedge_manager,
            order_manager=order_manager,
            safeguards=safeguards,
            journal=journal,
            logger=logger
        )
        
        return trade_manager

    except Exception as e:
        logger.critical(f"Initialization failed: {str(e)}", exc_info=True)
        raise

def main():
    """Main execution loop"""
    logger = configure_logger('main')
    logger.info("=== Starting IronFly Trading System ===")
    
    try:
        # Initialize
        trade_manager = initialize_components()
        
        # Main trading loop
        while True:
            try:
                # 1. Refresh all positions
                trade_manager.position_tracker.refresh_positions()
                logger.debug("Positions refreshed")
                
                # 2. Check for existing straddle
                if not trade_manager.has_active_straddle():
                    logger.info("No active straddle found - placing new straddle")
                    trade_manager.place_initial_straddle()
                
                # 3. Manage profitable legs
                profitable_legs = trade_manager.get_profitable_legs(
                    TRADE_CONFIG['profit_threshold']
                )
                for leg in profitable_legs:
                    logger.info(f"Managing profitable leg: {leg['symbol']}")
                    trade_manager.manage_profitable_leg(leg)
                
                # 4. Maintain hedges
                trade_manager.maintain_hedges()
                
                # 5. Handle expiring positions
                trade_manager.handle_expiring_positions()
                
                # 6. Generate daily snapshot
                trade_manager.generate_snapshot()
                
                # 7. Rate limiting
                trade_manager.safeguards.enforce_rate_limit()
                
            except KeyboardInterrupt:
                logger.info("Shutdown signal received")
                break
                
            except Exception as e:
                logger.error(f"Main loop error: {str(e)}", exc_info=True)
                trade_manager.safeguards.circuit_breaker.record_error()
                
                if trade_manager.safeguards.circuit_breaker.tripped:
                    logger.critical("Circuit breaker tripped! Entering cooldown")
                    time.sleep(300)  # 5 minute cooldown
                    trade_manager.safeguards.circuit_breaker.reset()
                
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}", exc_info=True)
        
    finally:
        logger.info("=== Trading System Stopped ===")
        if 'trade_manager' in locals():
            trade_manager.cleanup()

if __name__ == "__main__":
    import time
    main()
