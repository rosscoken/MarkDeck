"""
MarkDeck Core Engine

Main processing engine that orchestrates the conversion pipeline.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from markdeck.config.manager import ConfigManager
from markdeck.core.exceptions import MarkDeckError, ValidationError
from markdeck.core.pipeline import ProcessingPipeline
from markdeck.plugins.manager import PluginManager


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    output_path: Path
    pdf_path: Optional[Path] = None
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0


class MarkDeckEngine:
    """
    Main MarkDeck processing engine.
    
    Orchestrates the entire conversion process from Markdown to PowerPoint,
    managing configuration, plugins, and the processing pipeline.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        plugins_dir: Optional[Path] = None,
    ):
        """
        Initialize the MarkDeck engine.
        
        Args:
            config_path: Path to configuration file
            plugins_dir: Directory containing plugins
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.plugin_manager = PluginManager(plugins_dir)
        self.pipeline = ProcessingPipeline(
            config_manager=self.config_manager,
            plugin_manager=self.plugin_manager,
        )
        
        # Load configuration and plugins
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the engine components."""
        self.logger.info("Initializing MarkDeck engine")
        
        try:
            # Load configuration
            self.config_manager.load_config()
            self.logger.debug("Configuration loaded successfully")
            
            # Initialize plugins
            self.plugin_manager.discover_plugins()
            self.plugin_manager.load_plugins()
            self.logger.debug(f"Loaded {len(self.plugin_manager.plugins)} plugins")
            
            # Initialize pipeline
            self.pipeline.initialize()
            self.logger.debug("Processing pipeline initialized")
            
        except Exception as e:
            raise MarkDeckError(f"Failed to initialize engine: {e}")
    
    def process(
        self,
        input_path: Path,
        output_path: Path,
        theme: str = "default",
        theme_dir: Optional[Path] = None,
        export_pdf: bool = False,
        dry_run: bool = False,
    ) -> ProcessingResult:
        """
        Process a Markdown file into a PowerPoint presentation.
        
        Args:
            input_path: Path to input Markdown file
            output_path: Path for output PowerPoint file
            theme: Theme name or path to theme file
            theme_dir: Directory containing theme files
            export_pdf: Whether to also export to PDF
            dry_run: Parse and validate without generating output
            
        Returns:
            ProcessingResult with output information
            
        Raises:
            MarkDeckError: If processing fails
        """
        self.logger.info(f"Processing {input_path} -> {output_path}")
        
        # Validate inputs
        self._validate_inputs(input_path, output_path, theme, theme_dir)
        
        # Process through pipeline
        result = self.pipeline.process(
            input_path=input_path,
            output_path=output_path,
            theme=theme,
            theme_dir=theme_dir,
            export_pdf=export_pdf,
            dry_run=dry_run,
        )
        
        self.logger.info(f"Processing completed successfully")
        return result
    
    def validate_theme(
        self,
        theme: str,
        theme_dir: Optional[Path] = None,
    ) -> bool:
        """
        Validate a theme configuration.
        
        Args:
            theme: Theme name or path to theme file
            theme_dir: Directory containing theme files
            
        Returns:
            True if theme is valid
            
        Raises:
            MarkDeckError: If theme validation fails
        """
        self.logger.info(f"Validating theme: {theme}")
        
        try:
            # Validate theme through pipeline
            self.pipeline.validate_theme(theme, theme_dir)
            self.logger.info("Theme validation successful")
            return True
            
        except Exception as e:
            raise MarkDeckError(f"Theme validation failed: {e}")
    
    def _validate_inputs(
        self,
        input_path: Path,
        output_path: Path,
        theme: str,
        theme_dir: Optional[Path],
    ) -> None:
        """
        Validate input parameters.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            theme: Theme name or path
            theme_dir: Theme directory
            
        Raises:
            ValidationError: If validation fails
        """
        # Check input file exists
        if not input_path.exists():
            raise ValidationError(f"Input file not found: {input_path}")
        
        if not input_path.is_file():
            raise ValidationError(f"Input path is not a file: {input_path}")
        
        # Check input file extension
        if input_path.suffix.lower() not in [".md", ".markdown"]:
            raise ValidationError(f"Input file must be a Markdown file: {input_path}")
        
        # Check output directory exists or can be created
        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(f"Cannot create output directory: {e}")
        
        # Check theme directory if specified
        if theme_dir and not theme_dir.exists():
            raise ValidationError(f"Theme directory not found: {theme_dir}")
        
        self.logger.debug("Input validation successful")
    
    def get_available_themes(self, theme_dir: Optional[Path] = None) -> list:
        """
        Get list of available themes.
        
        Args:
            theme_dir: Directory to search for themes
            
        Returns:
            List of available theme names
        """
        return self.pipeline.get_available_themes(theme_dir)
    
    def get_plugin_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about loaded plugins.
        
        Returns:
            Dictionary of plugin information
        """
        return self.plugin_manager.get_plugin_info()
    
    def shutdown(self) -> None:
        """Shutdown the engine and cleanup resources."""
        self.logger.info("Shutting down MarkDeck engine")
        
        try:
            self.plugin_manager.shutdown()
            self.pipeline.shutdown()
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")