"""
MarkDeck Logging Configuration

Centralized logging setup and configuration for MarkDeck.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    verbosity: int = 0,
    log_file: Optional[Path] = None,
    console: Optional[Console] = None,
) -> None:
    """
    Setup logging configuration for MarkDeck.
    
    Args:
        verbosity: Verbosity level (0-3)
        log_file: Optional file path for logging
        console: Optional Rich console instance
    """
    # Determine log level based on verbosity
    if verbosity == 0:
        level = logging.WARNING
    elif verbosity == 1:
        level = logging.INFO
    elif verbosity == 2:
        level = logging.DEBUG
    else:  # verbosity >= 3
        level = logging.DEBUG
    
    # Create console handler with Rich formatting
    if console is None:
        console = Console(stderr=True)
    
    console_handler = RichHandler(
        console=console,
        show_time=verbosity >= 2,
        show_path=verbosity >= 3,
        markup=True,
        rich_tracebacks=True,
    )
    console_handler.setLevel(level)
    
    # Create formatter
    if verbosity >= 2:
        console_format = "%(message)s"
    else:
        console_format = "%(message)s"
    
    console_handler.setFormatter(logging.Formatter(console_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        file_handler.setFormatter(logging.Formatter(file_format))
        root_logger.addHandler(file_handler)
    
    # Configure third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")