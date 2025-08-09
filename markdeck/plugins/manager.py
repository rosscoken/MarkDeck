"""
Plugin Manager

Handles plugin discovery and loading.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List

from markdeck.core.exceptions import MarkDeckError


class PluginManager:
    """Manages MarkDeck plugins."""
    
    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir
        self.plugins = {}
    
    def discover_plugins(self) -> List[str]:
        """Discover available plugins."""
        # For MVP, no plugin discovery
        return []
    
    def load_plugins(self) -> None:
        """Load discovered plugins."""
        # For MVP, no plugin loading
        pass
    
    def get_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about loaded plugins."""
        return {}
    
    def shutdown(self) -> None:
        """Shutdown plugin manager."""
        pass