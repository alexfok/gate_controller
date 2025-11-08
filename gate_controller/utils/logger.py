"""Logging utility for gate controller."""

import logging
import os
from typing import Optional


def get_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Get or create a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Set level
        level_str = level or os.getenv('LOG_LEVEL', 'INFO')
        logger.setLevel(getattr(logging, level_str.upper(), logging.INFO))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(logging.DEBUG)
                file_format = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_format)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to create file handler for {log_file}: {e}")
    
    return logger

