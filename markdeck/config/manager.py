"""
Configuration Manager

Handles loading and managing configuration from files.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
import yaml
import toml

from markdeck.core.exceptions import MarkDeckError


class ConfigManager:
    """Manages MarkDeck configuration."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.config = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        if self.config_path and self.config_path.exists():
            try:
                if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    with open(self.config_path, 'r') as f:
                        self.config = yaml.safe_load(f) or {}
                elif self.config_path.suffix.lower() == '.toml':
                    with open(self.config_path, 'r') as f:
                        self.config = toml.load(f)
                elif self.config_path.suffix.lower() == '.json':
                    with open(self.config_path, 'r') as f:
                        self.config = json.load(f)
                else:
                    raise MarkDeckError(f"Unsupported config file format: {self.config_path}")
            except Exception as e:
                raise MarkDeckError(f"Failed to load config from {self.config_path}: {e}")
        else:
            # Use defaults
            self.config = self._get_default_config()
        
        return self.config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "theme": "default",
            "output_format": "pptx",
            "slide": {
                "heading_levels": [1, 2]
            },
            "image": {
                "max_width": 80,
                "max_height": 60
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value