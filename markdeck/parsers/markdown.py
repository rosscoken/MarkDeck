"""
MarkDeck Markdown Parser

Parses Markdown files using Pandoc and extracts presentation structure.
"""

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from markdeck.core.exceptions import ParseError
from markdeck.utils.logging import LoggerMixin
from markdeck.plugins.base import ParserPlugin


@dataclass
class SlideContent:
    """Represents content for a single slide."""
    title: str = ""
    content: List[Dict[str, Any]] = field(default_factory=list)
    speaker_notes: str = ""
    slide_type: str = "content"  # title, content, section
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Represents a parsed Markdown document."""
    structure: List[SlideContent] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_ast: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class MarkdownParser(LoggerMixin):
    """
    Main Markdown parser using Pandoc for AST generation.
    
    Converts Markdown files to presentation structures by:
    1. Using Pandoc to parse Markdown into AST
    2. Extracting speaker notes from HTML comments
    3. Mapping content to slide structure
    4. Supporting images, code blocks, tables, and lists
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        plugins: Optional[List[ParserPlugin]] = None,
    ):
        """
        Initialize the Markdown parser.
        
        Args:
            config: Parser configuration
            plugins: List of parser plugins
        """
        self.config = config or {}
        self.plugins = plugins or []
        
        # Configuration options
        self.slide_break_pattern = self.config.get("slide_break_pattern", r"^---\s*$")
        self.speaker_note_pattern = self.config.get(
            "speaker_note_pattern", 
            r"<!--\s*Speaker note:\s*(.*?)\s*-->"
        )
        self.pandoc_options = self.config.get("pandoc_options", [])
        
        self.logger.debug(f"Initialized MarkdownParser with {len(self.plugins)} plugins")
    
    def parse_file(self, file_path: Path) -> ParsedDocument:
        """
        Parse a Markdown file into presentation structure.
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            ParsedDocument with slide structure
            
        Raises:
            ParseError: If parsing fails
        """
        self.logger.info(f"Parsing Markdown file: {file_path}")
        
        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            return self.parse_content(content, str(file_path))
            
        except Exception as e:
            raise ParseError(f"Failed to parse file {file_path}: {e}")
    
    def parse_content(self, content: str, source_name: str = "<string>") -> ParsedDocument:
        """
        Parse Markdown content into presentation structure.
        
        Args:
            content: Markdown content string
            source_name: Name of source for error reporting
            
        Returns:
            ParsedDocument with slide structure
            
        Raises:
            ParseError: If parsing fails
        """
        self.logger.debug(f"Parsing content from {source_name}")
        
        try:
            # Extract speaker notes before Pandoc processing
            content, speaker_notes_map = self._extract_speaker_notes(content)
            
            # Parse with Pandoc
            ast = self._parse_with_pandoc(content)
            
            # Extract document metadata
            document_metadata = self._extract_document_metadata(ast)
            
            # Split content into slides
            slides = self._split_into_slides(ast, speaker_notes_map)
            
            # Apply plugins
            slides = self._apply_parser_plugins(slides, ast)
            
            # Create parsed document
            parsed_doc = ParsedDocument(
                structure=slides,
                metadata=document_metadata,
                raw_ast=ast,
                errors=[]
            )
            
            self.logger.info(f"Successfully parsed {len(slides)} slides from {source_name}")
            return parsed_doc
            
        except Exception as e:
            raise ParseError(f"Failed to parse content from {source_name}: {e}")
    
    def _parse_with_pandoc(self, content: str) -> Dict[str, Any]:
        """
        Parse Markdown content using Pandoc.
        
        Args:
            content: Markdown content
            
        Returns:
            Pandoc AST as dictionary
            
        Raises:
            ParseError: If Pandoc parsing fails
        """
        try:
            # Build Pandoc command
            cmd = [
                "pandoc",
                "--from", "markdown",
                "--to", "json",
                "--standalone"
            ] + self.pandoc_options
            
            # Run Pandoc
            result = subprocess.run(
                cmd,
                input=content,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON output
            ast = json.loads(result.stdout)
            self.logger.debug("Successfully parsed content with Pandoc")
            return ast
            
        except subprocess.CalledProcessError as e:
            raise ParseError(f"Pandoc parsing failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse Pandoc JSON output: {e}")
        except FileNotFoundError:
            raise ParseError("Pandoc not found. Please install Pandoc to use MarkDeck.")
    
    def _extract_speaker_notes(self, content: str) -> Tuple[str, Dict[int, str]]:
        """
        Extract speaker notes from HTML comments.
        
        Args:
            content: Markdown content
            
        Returns:
            Tuple of (content without notes, line -> note mapping)
        """
        speaker_notes_map = {}
        lines = content.split('\n')
        cleaned_lines = []
        
        for line_num, line in enumerate(lines, 1):
            # Check for speaker note comment
            match = re.search(self.speaker_note_pattern, line, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract note content
                note_content = match.group(1).strip()
                speaker_notes_map[line_num] = note_content
                
                # Remove the comment from the line
                cleaned_line = re.sub(self.speaker_note_pattern, '', line, flags=re.IGNORECASE | re.DOTALL).strip()
                if cleaned_line:
                    cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines)
        self.logger.debug(f"Extracted {len(speaker_notes_map)} speaker notes")
        return cleaned_content, speaker_notes_map
    
    def _extract_document_metadata(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from Pandoc AST.
        
        Args:
            ast: Pandoc AST
            
        Returns:
            Document metadata dictionary
        """
        metadata = {}
        
        # Extract Pandoc metadata
        if "meta" in ast:
            for key, value in ast["meta"].items():
                metadata[key] = self._extract_meta_value(value)
        
        # Extract additional metadata from first heading
        blocks = ast.get("blocks", [])
        if blocks and blocks[0].get("t") == "Header":
            header = blocks[0]
            if header.get("c", [None, None, None])[0] == 1:  # Level 1 header
                title_inlines = header.get("c", [None, None, []])[2]
                metadata["title"] = self._extract_text_from_inlines(title_inlines)
        
        return metadata
    
    def _extract_meta_value(self, meta_value: Dict[str, Any]) -> Any:
        """Extract value from Pandoc metadata."""
        if isinstance(meta_value, dict):
            if meta_value.get("t") == "MetaString":
                return meta_value.get("c", "")
            elif meta_value.get("t") == "MetaInlines":
                return self._extract_text_from_inlines(meta_value.get("c", []))
            elif meta_value.get("t") == "MetaBool":
                return meta_value.get("c", False)
            elif meta_value.get("t") == "MetaList":
                return [self._extract_meta_value(item) for item in meta_value.get("c", [])]
        return str(meta_value)
    
    def _extract_text_from_inlines(self, inlines: List[Dict[str, Any]]) -> str:
        """Extract plain text from Pandoc inline elements."""
        text_parts = []
        for inline in inlines:
            if inline.get("t") == "Str":
                text_parts.append(inline.get("c", ""))
            elif inline.get("t") == "Space":
                text_parts.append(" ")
            elif inline.get("t") == "SoftBreak":
                text_parts.append(" ")
            elif inline.get("t") in ["Emph", "Strong", "Code"]:
                # Extract text from formatted content
                nested_inlines = inline.get("c", [])
                if isinstance(nested_inlines, list):
                    text_parts.append(self._extract_text_from_inlines(nested_inlines))
                else:
                    text_parts.append(str(nested_inlines))
        return "".join(text_parts)
    
    def _split_into_slides(
        self, 
        ast: Dict[str, Any], 
        speaker_notes_map: Dict[int, str]
    ) -> List[SlideContent]:
        """
        Split AST blocks into slides based on headers and horizontal rules.
        
        Args:
            ast: Pandoc AST
            speaker_notes_map: Mapping of line numbers to speaker notes
            
        Returns:
            List of SlideContent objects
        """
        slides = []
        current_slide = SlideContent()
        blocks = ast.get("blocks", [])
        
        for block in blocks:
            block_type = block.get("t")
            
            if block_type == "Header":
                # Headers start new slides
                level, attributes, inlines = block.get("c", [1, [], []])
                
                # Save current slide if it has content
                if current_slide.title or current_slide.content:
                    slides.append(current_slide)
                
                # Start new slide
                current_slide = SlideContent()
                current_slide.title = self._extract_text_from_inlines(inlines)
                
                # Determine slide type based on header level
                if level == 1:
                    current_slide.slide_type = "title"
                elif level == 2:
                    current_slide.slide_type = "section"
                else:
                    current_slide.slide_type = "content"
                
                # Store header metadata
                current_slide.metadata["header_level"] = level
                current_slide.metadata["attributes"] = attributes
                
            elif block_type == "HorizontalRule":
                # Horizontal rules also start new slides
                if current_slide.title or current_slide.content:
                    slides.append(current_slide)
                current_slide = SlideContent()
                
            else:
                # Add block to current slide content
                current_slide.content.append(block)
        
        # Add final slide
        if current_slide.title or current_slide.content:
            slides.append(current_slide)
        
        # Associate speaker notes with slides
        self._associate_speaker_notes(slides, speaker_notes_map)
        
        self.logger.debug(f"Split content into {len(slides)} slides")
        return slides
    
    def _associate_speaker_notes(
        self, 
        slides: List[SlideContent], 
        speaker_notes_map: Dict[int, str]
    ) -> None:
        """
        Associate speaker notes with slides based on proximity.
        
        Args:
            slides: List of slides to update
            speaker_notes_map: Mapping of line numbers to speaker notes
        """
        # Simple association: assign notes to the previous slide
        # This could be improved with more sophisticated line tracking
        for slide in slides:
            # For now, combine all speaker notes into each slide
            # A more sophisticated implementation would track line numbers
            if speaker_notes_map:
                notes = list(speaker_notes_map.values())
                slide.speaker_notes = " ".join(notes)
                break  # Only assign to first slide for now
    
    def _apply_parser_plugins(
        self, 
        slides: List[SlideContent], 
        ast: Dict[str, Any]
    ) -> List[SlideContent]:
        """
        Apply parser plugins to modify slide content.
        
        Args:
            slides: List of slides
            ast: Original AST
            
        Returns:
            Modified slides
        """
        for plugin in self.plugins:
            try:
                # Apply plugin to each slide
                for slide in slides:
                    for i, block in enumerate(slide.content):
                        if plugin.supports_element_type(block.get("t", "")):
                            slide.content[i] = plugin.parse_element(block)
                
                # Extract additional metadata
                plugin_metadata = plugin.extract_metadata(ast)
                for slide in slides:
                    slide.metadata.update(plugin_metadata)
                    
            except Exception as e:
                self.logger.warning(f"Plugin {plugin.name} failed: {e}")
        
        return slides
    
    def shutdown(self) -> None:
        """Cleanup parser resources."""
        for plugin in self.plugins:
            try:
                plugin.shutdown()
            except Exception as e:
                self.logger.warning(f"Error shutting down plugin {plugin.name}: {e}")