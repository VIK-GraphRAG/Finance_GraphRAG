"""
Structured logging utility for Finance GraphRAG
Provides consistent, leveled logging with timestamps
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class StructuredLogger:
    """
    Structured logger with file and console output
    Follows cursorrules: structured logging + user-friendly errors
    """
    
    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers.clear()
        
        # Console handler (user-friendly format)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            '%(levelname)s | %(name)s | %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (detailed format)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str) -> None:
        """Log info level message"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log warning level message"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        """Log error level message"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str) -> None:
        """Log debug level message"""
        self.logger.debug(message)
    
    def critical(self, message: str, exc_info: bool = True) -> None:
        """Log critical level message"""
        self.logger.critical(message, exc_info=exc_info)


# Singleton logger instances
_loggers: dict[str, StructuredLogger] = {}


def get_logger(name: str, log_file: Optional[str] = None) -> StructuredLogger:
    """
    Get or create a structured logger instance
    
    Args:
        name: Logger name (typically module name)
        log_file: Optional log file path
    
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, log_file)
    return _loggers[name]
