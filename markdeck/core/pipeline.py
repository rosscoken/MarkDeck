"""
MarkDeck Processing Pipeline

Orchestrates the complete processing pipeline from Markdown to PowerPoint.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

from markdeck.config.manager import ConfigManager
from markdeck.core.exceptions import MarkDeckError, ProcessingError
from markdeck.plugins.manager import PluginManager


@dataclass
class ProcessingResult:
    """Result of a processing operation."""
    output_path: Path
    pdf_path: Optional[Path] = None
    metadata: Dict[str, Any] = None
    processing_time: float = 0.0
    slide_count: int = 0


class ProcessingPipeline:
    """
    Main processing pipeline that orchestrates the conversion process.
    
    Coordinates between parsers, theme engine, generators, and exporters
    to convert Markdown files into PowerPoint presentations.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        plugin_manager: PluginManager,
    ):
        """
        Initialize the processing pipeline.
        
        Args:
            config_manager: Configuration manager instance
            plugin_manager: Plugin manager instance
        """
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        
        # Components will be initialized lazily
        self._parser = None
        self._theme_engine = None
        self._generator = None
        self._exporter = None
    
    def initialize(self) -> None:
        """Initialize pipeline components."""
        self.logger.debug("Initializing processing pipeline")
        
        try:
            # Import and initialize components
            from markdeck.parsers.markdown import MarkdownParser
            from markdeck.themes.engine import ThemeEngine
            from markdeck.generators.pptx_generator import PPTXGenerator
            from markdeck.exporters.pdf_exporter import PDFExporter
            
            self._parser = MarkdownParser(
                config=self.config_manager.get_parser_config(),
                plugins=self.plugin_manager.get_plugins_by_type("parser"),
            )
            
            self._theme_engine = ThemeEngine(
                config=self.config_manager.get_theme_config(),
                plugins=self.plugin_manager.get_plugins_by_type("theme"),
            )
            
            self._generator = PPTXGenerator(
                config=self.config_manager.get_generator_config(),
                plugins=self.plugin_manager.get_plugins_by_type("generator"),
            )
            
            self._exporter = PDFExporter(
                config=self.config_manager.get_exporter_config(),
                plugins=self.plugin_manager.get_plugins_by_type("exporter"),
            )
            
            self.logger.debug("Pipeline components initialized successfully")
            
        except Exception as e:
            raise MarkDeckError(f"Failed to initialize pipeline: {e}")
    
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
        Process a Markdown file through the complete pipeline.
        
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
        start_time = time.time()
        self.logger.info(f"Starting pipeline processing: {input_path}")
        
        try:
            # Step 1: Parse Markdown
            self.logger.debug("Step 1: Parsing Markdown")
            parsed_content = self._parser.parse_file(input_path)
            self.logger.info(f"Parsed {len(parsed_content.structure)} slides")
            
            # Step 2: Load and process theme
            self.logger.debug("Step 2: Processing theme")
            theme_config = self._theme_engine.load_theme(theme, theme_dir)
            processed_theme = self._theme_engine.process_theme(
                theme_config, 
                parsed_content.metadata
            )
            self.logger.info(f"Loaded theme: {processed_theme.metadata.name}")
            
            # Step 3: Generate presentation
            self.logger.debug("Step 3: Generating presentation")
            if not dry_run:
                presentation = self._generator.generate_presentation(
                    content=parsed_content,
                    theme=processed_theme,
                    output_path=output_path,
                )
                self.logger.info(f"Generated presentation: {output_path}")
            else:
                presentation = None
                self.logger.info("Dry run: skipped presentation generation")
            
            # Step 4: Export to PDF if requested
            pdf_path = None
            if export_pdf and not dry_run:
                self.logger.debug("Step 4: Exporting to PDF")
                pdf_path = output_path.with_suffix(".pdf")
                self._exporter.export_to_pdf(presentation, pdf_path)
                self.logger.info(f"Exported PDF: {pdf_path}")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create result
            result = ProcessingResult(
                output_path=output_path,
                pdf_path=pdf_path,
                metadata=parsed_content.metadata,
                processing_time=processing_time,
                slide_count=len(parsed_content.structure),
            )
            
            self.logger.info(
                f"Pipeline completed successfully in {processing_time:.2f}s"
            )
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Pipeline failed after {processing_time:.2f}s: {e}")
            raise ProcessingError(f"Pipeline processing failed: {e}")
    
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
        self.logger.debug(f"Validating theme: {theme}")
        
        try:
            # Load theme
            theme_config = self._theme_engine.load_theme(theme, theme_dir)
            
            # Validate theme
            is_valid = self._theme_engine.validate_theme(theme_config)
            
            if is_valid:
                self.logger.info(f"Theme validation successful: {theme}")
            else:
                self.logger.error(f"Theme validation failed: {theme}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Theme validation error: {e}")
            raise MarkDeckError(f"Theme validation failed: {e}")
    
    def get_available_themes(self, theme_dir: Optional[Path] = None) -> list:
        """
        Get list of available themes.
        
        Args:
            theme_dir: Directory to search for themes
            
        Returns:
            List of available theme names
        """
        return self._theme_engine.get_available_themes(theme_dir)
    
    def shutdown(self) -> None:
        """Shutdown pipeline components and cleanup resources."""
        self.logger.debug("Shutting down processing pipeline")
        
        try:
            if self._parser:
                self._parser.shutdown()
            if self._theme_engine:
                self._theme_engine.shutdown()
            if self._generator:
                self._generator.shutdown()
            if self._exporter:
                self._exporter.shutdown()
                
        except Exception as e:
            self.logger.error(f"Error during pipeline shutdown: {e}")


class ProcessingError(MarkDeckError):
    """Exception raised when pipeline processing fails."""
    pass