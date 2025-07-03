"""
MarkDeck Plugin Base Classes

Base classes and interfaces for MarkDeck plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MarkDeckPlugin(ABC):
    """Base plugin interface for all MarkDeck plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass
    
    @property
    def description(self) -> str:
        """Plugin description."""
        return ""
    
    @property
    def author(self) -> str:
        """Plugin author."""
        return ""
    
    @property
    def dependencies(self) -> List[str]:
        """Plugin dependencies."""
        return []
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        pass
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process data through plugin.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
    
    def shutdown(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        return True


class ParserPlugin(MarkDeckPlugin):
    """Base class for markdown parser plugins."""
    
    @abstractmethod
    def parse_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a specific markdown element.
        
        Args:
            element: Markdown element from Pandoc AST
            
        Returns:
            Processed element
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from document.
        
        Args:
            document: Pandoc document
            
        Returns:
            Extracted metadata
        """
        pass
    
    def supports_element_type(self, element_type: str) -> bool:
        """
        Check if plugin supports a specific element type.
        
        Args:
            element_type: Pandoc element type
            
        Returns:
            True if supported
        """
        return False


class GeneratorPlugin(MarkDeckPlugin):
    """Base class for slide generator plugins."""
    
    @abstractmethod
    def generate_slide(
        self,
        content: Dict[str, Any],
        theme: Dict[str, Any],
        slide_index: int,
    ) -> Any:
        """
        Generate a slide from content.
        
        Args:
            content: Slide content
            theme: Theme configuration
            slide_index: Slide index in presentation
            
        Returns:
            Generated slide object
        """
        pass
    
    @abstractmethod
    def supports_slide_type(self, slide_type: str) -> bool:
        """
        Check if plugin supports a specific slide type.
        
        Args:
            slide_type: Slide type identifier
            
        Returns:
            True if supported
        """
        pass
    
    def post_process_slide(self, slide: Any, content: Dict[str, Any]) -> Any:
        """
        Post-process generated slide.
        
        Args:
            slide: Generated slide object
            content: Original content
            
        Returns:
            Post-processed slide
        """
        return slide


class ExporterPlugin(MarkDeckPlugin):
    """Base class for export format plugins."""
    
    @property
    @abstractmethod
    def output_format(self) -> str:
        """Output format identifier."""
        pass
    
    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Output file extension."""
        pass
    
    @abstractmethod
    def export(
        self,
        presentation: Any,
        output_path: str,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Export presentation to format.
        
        Args:
            presentation: Presentation object
            output_path: Output file path
            options: Export options
            
        Returns:
            Path to exported file
        """
        pass
    
    def validate_options(self, options: Dict[str, Any]) -> bool:
        """
        Validate export options.
        
        Args:
            options: Export options
            
        Returns:
            True if options are valid
        """
        return True


class ThemePlugin(MarkDeckPlugin):
    """Base class for theme processor plugins."""
    
    @abstractmethod
    def process_theme(self, theme_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process theme configuration.
        
        Args:
            theme_config: Raw theme configuration
            
        Returns:
            Processed theme configuration
        """
        pass
    
    @abstractmethod
    def validate_theme(self, theme_config: Dict[str, Any]) -> bool:
        """
        Validate theme configuration.
        
        Args:
            theme_config: Theme configuration
            
        Returns:
            True if theme is valid
        """
        pass
    
    def supports_theme_version(self, version: str) -> bool:
        """
        Check if plugin supports a specific theme version.
        
        Args:
            version: Theme schema version
            
        Returns:
            True if supported
        """
        return True
    
    def compile_programmatic_elements(
        self,
        theme_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compile programmatic theme elements.
        
        Args:
            theme_config: Theme configuration with scripts
            
        Returns:
            Compiled theme configuration
        """
        return theme_config


class PluginRegistry:
    """Registry for managing plugin instances."""
    
    def __init__(self):
        self._plugins: Dict[str, MarkDeckPlugin] = {}
        self._plugins_by_type: Dict[str, List[MarkDeckPlugin]] = {
            "parser": [],
            "generator": [],
            "exporter": [],
            "theme": [],
        }
    
    def register(self, plugin: MarkDeckPlugin) -> None:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin to register
        """
        self._plugins[plugin.name] = plugin
        
        # Add to type-specific lists
        if isinstance(plugin, ParserPlugin):
            self._plugins_by_type["parser"].append(plugin)
        elif isinstance(plugin, GeneratorPlugin):
            self._plugins_by_type["generator"].append(plugin)
        elif isinstance(plugin, ExporterPlugin):
            self._plugins_by_type["exporter"].append(plugin)
        elif isinstance(plugin, ThemePlugin):
            self._plugins_by_type["theme"].append(plugin)
    
    def get_plugin(self, name: str) -> Optional[MarkDeckPlugin]:
        """Get plugin by name."""
        return self._plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: str) -> List[MarkDeckPlugin]:
        """Get all plugins of a specific type."""
        return self._plugins_by_type.get(plugin_type, [])
    
    def get_all_plugins(self) -> Dict[str, MarkDeckPlugin]:
        """Get all registered plugins."""
        return self._plugins.copy()
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            name: Plugin name
            
        Returns:
            True if plugin was unregistered
        """
        if name in self._plugins:
            plugin = self._plugins.pop(name)
            
            # Remove from type-specific lists
            for plugin_list in self._plugins_by_type.values():
                if plugin in plugin_list:
                    plugin_list.remove(plugin)
            
            return True
        return False