import logging
import os
from logging.handlers import TimedRotatingFileHandler

def configure_logger(name, log_level=logging.INFO):
    """Configure logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Create logs directory if not exists
    os.makedirs('logs', exist_ok=True)
    
    # File handler (daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename='logs/trading_system.log',
        when='D',
        interval=1,
        backupCount=7
    )
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
