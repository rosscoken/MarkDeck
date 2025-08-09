"""
MarkDeck Pandoc Bridge

Bridge interface for Pandoc integration and AST manipulation.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging


class ParseError(Exception):
    """Exception raised when parsing fails."""
    pass


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


class PandocBridge(LoggerMixin):
    """
    Bridge interface for Pandoc operations.
    
    Provides utilities for:
    - Running Pandoc with various options
    - Converting between formats
    - Manipulating Pandoc AST
    - Extracting specific elements
    """
    
    def __init__(self, pandoc_path: str = "pandoc"):
        """
        Initialize Pandoc bridge.
        
        Args:
            pandoc_path: Path to Pandoc executable
        """
        self.pandoc_path = pandoc_path
        self._verify_pandoc()
    
    def _verify_pandoc(self) -> None:
        """Verify Pandoc is available and get version."""
        try:
            result = subprocess.run(
                [self.pandoc_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version_line = result.stdout.split('\n')[0]
            self.logger.info(f"Found {version_line}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise ParseError(f"Pandoc not found at '{self.pandoc_path}'. Please install Pandoc.")
    
    def convert_to_ast(
        self,
        content: str,
        input_format: str = "markdown",
        options: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert content to Pandoc AST.
        
        Args:
            content: Input content
            input_format: Input format (markdown, html, etc.)
            options: Additional Pandoc options
            
        Returns:
            Pandoc AST as dictionary
            
        Raises:
            ParseError: If conversion fails
        """
        cmd = [
            self.pandoc_path,
            "--from", input_format,
            "--to", "json",
            "--standalone"
        ]
        
        if options:
            cmd.extend(options)
        
        try:
            result = subprocess.run(
                cmd,
                input=content,
                capture_output=True,
                text=True,
                check=True
            )
            
            ast = json.loads(result.stdout)
            self.logger.debug(f"Successfully converted {len(content)} chars to AST")
            return ast
            
        except subprocess.CalledProcessError as e:
            raise ParseError(f"Pandoc conversion failed: {e.stderr}")
        except json.JSONDecodeError as e:
            raise ParseError(f"Failed to parse Pandoc JSON output: {e}")
    
    def convert_from_ast(
        self,
        ast: Dict[str, Any],
        output_format: str = "html",
        options: Optional[List[str]] = None
    ) -> str:
        """
        Convert Pandoc AST to specified format.
        
        Args:
            ast: Pandoc AST dictionary
            output_format: Output format (html, latex, etc.)
            options: Additional Pandoc options
            
        Returns:
            Converted content as string
            
        Raises:
            ParseError: If conversion fails
        """
        cmd = [
            self.pandoc_path,
            "--from", "json",
            "--to", output_format
        ]
        
        if options:
            cmd.extend(options)
        
        try:
            ast_json = json.dumps(ast)
            
            result = subprocess.run(
                cmd,
                input=ast_json,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.debug(f"Successfully converted AST to {output_format}")
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            raise ParseError(f"Pandoc conversion failed: {e.stderr}")
        except json.JSONEncodeError as e:
            raise ParseError(f"Failed to encode AST to JSON: {e}")
    
    def convert_file(
        self,
        input_path: Path,
        output_path: Path,
        input_format: Optional[str] = None,
        output_format: Optional[str] = None,
        options: Optional[List[str]] = None
    ) -> None:
        """
        Convert file using Pandoc.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            input_format: Input format (auto-detected if None)
            output_format: Output format (auto-detected if None)
            options: Additional Pandoc options
            
        Raises:
            ParseError: If conversion fails
        """
        cmd = [self.pandoc_path]
        
        if input_format:
            cmd.extend(["--from", input_format])
        
        if output_format:
            cmd.extend(["--to", output_format])
        
        cmd.extend([
            "--output", str(output_path),
            str(input_path)
        ])
        
        if options:
            cmd.extend(options)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.logger.debug(f"Successfully converted {input_path} to {output_path}")
            
        except subprocess.CalledProcessError as e:
            raise ParseError(f"File conversion failed: {e.stderr}")
    
    def extract_metadata(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract metadata from Pandoc AST.
        
        Args:
            ast: Pandoc AST
            
        Returns:
            Extracted metadata
        """
        metadata = {}
        
        if "meta" in ast:
            for key, value in ast["meta"].items():
                metadata[key] = self._extract_meta_value(value)
        
        return metadata
    
    def _extract_meta_value(self, meta_value: Dict[str, Any]) -> Any:
        """Extract value from Pandoc metadata structure."""
        if isinstance(meta_value, dict):
            meta_type = meta_value.get("t")
            meta_content = meta_value.get("c")
            
            if meta_type == "MetaString":
                return meta_content
            elif meta_type == "MetaInlines":
                return self.extract_text_from_inlines(meta_content)
            elif meta_type == "MetaBool":
                return meta_content
            elif meta_type == "MetaList":
                return [self._extract_meta_value(item) for item in meta_content]
            elif meta_type == "MetaMap":
                return {k: self._extract_meta_value(v) for k, v in meta_content.items()}
        
        return str(meta_value)
    
    def extract_text_from_inlines(self, inlines: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Pandoc inline elements.
        
        Args:
            inlines: List of Pandoc inline elements
            
        Returns:
            Extracted plain text
        """
        text_parts = []
        
        for inline in inlines:
            if not isinstance(inline, dict):
                continue
                
            inline_type = inline.get("t")
            inline_content = inline.get("c")
            
            if inline_type == "Str":
                text_parts.append(inline_content)
            elif inline_type == "Space":
                text_parts.append(" ")
            elif inline_type == "SoftBreak":
                text_parts.append(" ")
            elif inline_type == "LineBreak":
                text_parts.append("\n")
            elif inline_type in ["Emph", "Strong", "Strikeout", "Superscript", "Subscript"]:
                if isinstance(inline_content, list):
                    text_parts.append(self.extract_text_from_inlines(inline_content))
            elif inline_type == "Code":
                # inline_content is [attributes, code_text]
                if isinstance(inline_content, list) and len(inline_content) >= 2:
                    text_parts.append(inline_content[1])
            elif inline_type == "Link":
                # inline_content is [attributes, link_text, target]
                if isinstance(inline_content, list) and len(inline_content) >= 2:
                    text_parts.append(self.extract_text_from_inlines(inline_content[1]))
            elif inline_type == "Image":
                # inline_content is [attributes, alt_text, target]
                if isinstance(inline_content, list) and len(inline_content) >= 2:
                    text_parts.append(self.extract_text_from_inlines(inline_content[1]))
        
        return "".join(text_parts)
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Pandoc block elements.
        
        Args:
            blocks: List of Pandoc block elements
            
        Returns:
            Extracted plain text
        """
        text_parts = []
        
        for block in blocks:
            if not isinstance(block, dict):
                continue
                
            block_type = block.get("t")
            block_content = block.get("c")
            
            if block_type == "Para":
                if isinstance(block_content, list):
                    text_parts.append(self.extract_text_from_inlines(block_content))
                    text_parts.append("\n\n")
            
            elif block_type == "Header":
                # block_content is [level, attributes, inlines]
                if isinstance(block_content, list) and len(block_content) >= 3:
                    text_parts.append(self.extract_text_from_inlines(block_content[2]))
                    text_parts.append("\n\n")
            
            elif block_type == "CodeBlock":
                # block_content is [attributes, code_text]
                if isinstance(block_content, list) and len(block_content) >= 2:
                    text_parts.append(block_content[1])
                    text_parts.append("\n\n")
            
            elif block_type in ["BulletList", "OrderedList"]:
                if isinstance(block_content, list):
                    for item in block_content:
                        if isinstance(item, list):
                            text_parts.append("- ")
                            text_parts.append(self.extract_text_from_blocks(item))
            
            elif block_type == "BlockQuote":
                if isinstance(block_content, list):
                    text_parts.append("> ")
                    text_parts.append(self.extract_text_from_blocks(block_content))
        
        return "".join(text_parts)
    
    def find_elements_by_type(
        self,
        ast: Dict[str, Any],
        element_type: str
    ) -> List[Dict[str, Any]]:
        """
        Find all elements of a specific type in AST.
        
        Args:
            ast: Pandoc AST
            element_type: Element type to find (e.g., "Image", "CodeBlock")
            
        Returns:
            List of matching elements
        """
        elements = []
        
        def traverse(obj):
            if isinstance(obj, dict):
                if obj.get("t") == element_type:
                    elements.append(obj)
                for value in obj.values():
                    traverse(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)
        
        traverse(ast)
        return elements
    
    def modify_ast(
        self,
        ast: Dict[str, Any],
        modifier_func: callable
    ) -> Dict[str, Any]:
        """
        Apply a modifier function to all elements in AST.
        
        Args:
            ast: Pandoc AST to modify
            modifier_func: Function that takes an element and returns modified element
            
        Returns:
            Modified AST
        """
        def traverse_and_modify(obj):
            if isinstance(obj, dict):
                # Apply modifier to this element
                modified_obj = modifier_func(obj)
                
                # Recursively modify children
                if isinstance(modified_obj, dict):
                    for key, value in modified_obj.items():
                        modified_obj[key] = traverse_and_modify(value)
                
                return modified_obj
            
            elif isinstance(obj, list):
                return [traverse_and_modify(item) for item in obj]
            
            else:
                return obj
        
        return traverse_and_modify(ast)
    
    def create_ast_element(
        self,
        element_type: str,
        content: Any,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Pandoc AST element.
        
        Args:
            element_type: Type of element to create
            content: Element content
            attributes: Optional attributes
            
        Returns:
            Pandoc AST element
        """
        element = {
            "t": element_type,
            "c": content
        }
        
        if attributes:
            # Some elements have attributes as part of content
            if element_type in ["Header", "CodeBlock", "Image", "Link"]:
                if isinstance(content, list) and len(content) > 0:
                    content[0] = attributes
                else:
                    element["c"] = [attributes, content]
        
        return element
    
    def validate_ast(self, ast: Dict[str, Any]) -> bool:
        """
        Validate that AST has correct structure.
        
        Args:
            ast: AST to validate
            
        Returns:
            True if AST is valid
        """
        try:
            # Check basic structure
            if not isinstance(ast, dict):
                return False
            
            if "pandoc-api-version" not in ast:
                return False
            
            if "blocks" not in ast:
                return False
            
            if not isinstance(ast["blocks"], list):
                return False
            
            # Try to convert back to JSON to verify structure
            json.dumps(ast)
            
            return True
            
        except Exception:
            return False