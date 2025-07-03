"""
MarkDeck Configuration Management

Configuration management and validation for MarkDeck.
"""

from markdeck.config.manager import ConfigManager
from markdeck.config.defaults import get_default_config

__all__ = [
    "ConfigManager",
    "get_default_config",
]