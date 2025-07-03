"""
MarkDeck Slide Mapper

Maps Markdown AST elements to slide layouts and handles content distribution.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from markdeck.core.exceptions import ParseError
from markdeck.utils.logging import LoggerMixin
from markdeck.parsers.markdown import SlideContent


@dataclass
class SlideLayout:
    """Represents a slide layout configuration."""
    layout_type: str
    max_content_blocks: int = 10
    supports_title: bool = True
    supports_subtitle: bool = False
    supports_images: bool = True
    supports_lists: bool = True
    supports_code: bool = True
    supports_tables: bool = True
    content_distribution: str = "auto"  # auto, split, single


@dataclass
class MappedSlide:
    """Represents a slide with mapped layout information."""
    content: SlideContent
    layout: SlideLayout
    overflow_content: List[Dict[str, Any]] = field(default_factory=list)
    estimated_size: int = 0


class SlideMapper(LoggerMixin):
    """
    Maps Markdown AST elements to appropriate slide layouts.
    
    Handles:
    - Mapping heading levels to slide types
    - Intelligent content distribution across slides
    - Layout selection based on content type
    - Content overflow handling
    """
    
    # Default layout configurations
    DEFAULT_LAYOUTS = {
        "title": SlideLayout(
            layout_type="title",
            max_content_blocks=2,
            supports_subtitle=True,
            content_distribution="single"
        ),
        "section": SlideLayout(
            layout_type="section",
            max_content_blocks=5,
            supports_subtitle=True,
            content_distribution="single"
        ),
        "content": SlideLayout(
            layout_type="content",
            max_content_blocks=8,
            content_distribution="auto"
        ),
        "content_image": SlideLayout(
            layout_type="content_image",
            max_content_blocks=6,
            content_distribution="split"
        ),
        "content_code": SlideLayout(
            layout_type="content_code",
            max_content_blocks=4,
            supports_tables=False,
            content_distribution="single"
        ),
        "content_table": SlideLayout(
            layout_type="content_table",
            max_content_blocks=3,
            supports_code=False,
            content_distribution="single"
        ),
        "content_list": SlideLayout(
            layout_type="content_list",
            max_content_blocks=6,
            content_distribution="auto"
        )
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the slide mapper.
        
        Args:
            config: Mapper configuration
        """
        self.config = config or {}
        
        # Load layout configurations
        self.layouts = self._load_layouts()
        
        # Configuration options
        self.max_content_per_slide = self.config.get("max_content_per_slide", 8)
        self.auto_split_large_content = self.config.get("auto_split_large_content", True)
        self.prefer_single_concept_slides = self.config.get("prefer_single_concept_slides", True)
        
        self.logger.debug(f"Initialized SlideMapper with {len(self.layouts)} layouts")
    
    def map_slides(self, slides: List[SlideContent]) -> List[MappedSlide]:
        """
        Map slides to appropriate layouts and handle content distribution.
        
        Args:
            slides: List of parsed slides
            
        Returns:
            List of mapped slides with layout information
        """
        self.logger.info(f"Mapping {len(slides)} slides to layouts")
        
        mapped_slides = []
        
        for slide in slides:
            # Determine appropriate layout
            layout = self._select_layout(slide)
            
            # Handle content distribution
            distributed_slides = self._distribute_content(slide, layout)
            
            mapped_slides.extend(distributed_slides)
        
        self.logger.info(f"Created {len(mapped_slides)} mapped slides")
        return mapped_slides
    
    def _load_layouts(self) -> Dict[str, SlideLayout]:
        """Load slide layout configurations."""
        layouts = {}
        
        # Start with default layouts
        layouts.update(self.DEFAULT_LAYOUTS)
        
        # Override with custom layouts from config
        custom_layouts = self.config.get("layouts", {})
        for name, layout_config in custom_layouts.items():
            layouts[name] = SlideLayout(**layout_config)
        
        return layouts
    
    def _select_layout(self, slide: SlideContent) -> SlideLayout:
        """
        Select the most appropriate layout for a slide.
        
        Args:
            slide: Slide content to analyze
            
        Returns:
            Selected layout
        """
        # Start with slide type mapping
        base_layout_name = self._map_slide_type_to_layout(slide.slide_type)
        
        # Analyze content to refine layout choice
        content_analysis = self._analyze_content(slide.content)
        
        # Select specialized layout based on content
        if content_analysis["has_images"] and content_analysis["image_count"] > 0:
            layout_name = "content_image"
        elif content_analysis["has_code_blocks"] and content_analysis["code_block_count"] > 0:
            layout_name = "content_code"
        elif content_analysis["has_tables"] and content_analysis["table_count"] > 0:
            layout_name = "content_table"
        elif content_analysis["has_lists"] and content_analysis["list_count"] > 2:
            layout_name = "content_list"
        else:
            layout_name = base_layout_name
        
        # Fall back to base layout if specialized layout doesn't exist
        if layout_name not in self.layouts:
            layout_name = base_layout_name
        
        self.logger.debug(f"Selected layout '{layout_name}' for slide: {slide.title[:50]}...")
        return self.layouts[layout_name]
    
    def _map_slide_type_to_layout(self, slide_type: str) -> str:
        """Map slide type to layout name."""
        mapping = {
            "title": "title",
            "section": "section",
            "content": "content"
        }
        return mapping.get(slide_type, "content")
    
    def _analyze_content(self, content: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze slide content to determine characteristics.
        
        Args:
            content: List of content blocks
            
        Returns:
            Analysis results
        """
        analysis = {
            "block_count": len(content),
            "has_images": False,
            "image_count": 0,
            "has_code_blocks": False,
            "code_block_count": 0,
            "has_tables": False,
            "table_count": 0,
            "has_lists": False,
            "list_count": 0,
            "estimated_size": 0,
            "complexity_score": 0
        }
        
        for block in content:
            block_type = block.get("t", "")
            
            # Count different content types
            if block_type == "Image":
                analysis["has_images"] = True
                analysis["image_count"] += 1
                analysis["estimated_size"] += 3  # Images take more space
            
            elif block_type == "CodeBlock":
                analysis["has_code_blocks"] = True
                analysis["code_block_count"] += 1
                analysis["estimated_size"] += 2  # Code blocks take more space
            
            elif block_type == "Table":
                analysis["has_tables"] = True
                analysis["table_count"] += 1
                analysis["estimated_size"] += 2  # Tables take more space
            
            elif block_type in ["BulletList", "OrderedList"]:
                analysis["has_lists"] = True
                analysis["list_count"] += 1
                
                # Count list items for complexity
                items = block.get("c", [])
                if isinstance(items, list):
                    analysis["estimated_size"] += len(items) * 0.5
            
            elif block_type == "Para":
                analysis["estimated_size"] += 1
            
            else:
                analysis["estimated_size"] += 0.5
        
        # Calculate complexity score
        analysis["complexity_score"] = (
            analysis["image_count"] * 2 +
            analysis["code_block_count"] * 3 +
            analysis["table_count"] * 3 +
            analysis["list_count"] * 1
        )
        
        return analysis
    
    def _distribute_content(
        self, 
        slide: SlideContent, 
        layout: SlideLayout
    ) -> List[MappedSlide]:
        """
        Distribute slide content across multiple slides if needed.
        
        Args:
            slide: Original slide content
            layout: Selected layout
            
        Returns:
            List of distributed slides
        """
        content = slide.content
        
        # Check if content fits in single slide
        if len(content) <= layout.max_content_blocks:
            # Content fits, create single mapped slide
            mapped_slide = MappedSlide(
                content=slide,
                layout=layout,
                estimated_size=self._estimate_content_size(content)
            )
            return [mapped_slide]
        
        # Content doesn't fit, need to distribute
        if not self.auto_split_large_content:
            # Don't split, just mark overflow
            mapped_slide = MappedSlide(
                content=slide,
                layout=layout,
                overflow_content=content[layout.max_content_blocks:],
                estimated_size=self._estimate_content_size(content)
            )
            # Trim content to fit
            slide.content = content[:layout.max_content_blocks]
            return [mapped_slide]
        
        # Split content into multiple slides
        return self._split_content(slide, layout)
    
    def _split_content(
        self, 
        slide: SlideContent, 
        layout: SlideLayout
    ) -> List[MappedSlide]:
        """
        Split slide content into multiple slides.
        
        Args:
            slide: Original slide
            layout: Layout to use
            
        Returns:
            List of split slides
        """
        content_blocks = slide.content
        slides = []
        
        # Determine split strategy based on layout
        if layout.content_distribution == "single":
            # Keep as single slide with overflow
            mapped_slide = MappedSlide(
                content=slide,
                layout=layout,
                overflow_content=content_blocks[layout.max_content_blocks:],
                estimated_size=self._estimate_content_size(content_blocks)
            )
            slide.content = content_blocks[:layout.max_content_blocks]
            slides.append(mapped_slide)
            
        elif layout.content_distribution == "split":
            # Split content evenly
            chunks = self._chunk_content(content_blocks, layout.max_content_blocks)
            
            for i, chunk in enumerate(chunks):
                # Create new slide for each chunk
                new_slide = SlideContent(
                    title=slide.title if i == 0 else f"{slide.title} (cont.)",
                    content=chunk,
                    speaker_notes=slide.speaker_notes if i == 0 else "",
                    slide_type=slide.slide_type,
                    metadata=slide.metadata.copy()
                )
                
                mapped_slide = MappedSlide(
                    content=new_slide,
                    layout=layout,
                    estimated_size=self._estimate_content_size(chunk)
                )
                slides.append(mapped_slide)
                
        else:  # auto
            # Smart splitting based on content type
            slides = self._auto_split_content(slide, layout)
        
        return slides
    
    def _auto_split_content(
        self, 
        slide: SlideContent, 
        layout: SlideLayout
    ) -> List[MappedSlide]:
        """
        Automatically split content using intelligent grouping.
        
        Args:
            slide: Original slide
            layout: Layout to use
            
        Returns:
            List of intelligently split slides
        """
        content_blocks = slide.content
        slides = []
        
        # Group content by logical sections
        content_groups = self._group_content_logically(content_blocks)
        
        current_group = []
        current_size = 0
        
        for group in content_groups:
            group_size = len(group)
            
            # Check if adding this group would exceed capacity
            if current_size + group_size > layout.max_content_blocks and current_group:
                # Create slide with current group
                new_slide = SlideContent(
                    title=slide.title if not slides else f"{slide.title} (cont.)",
                    content=current_group,
                    speaker_notes=slide.speaker_notes if not slides else "",
                    slide_type=slide.slide_type,
                    metadata=slide.metadata.copy()
                )
                
                mapped_slide = MappedSlide(
                    content=new_slide,
                    layout=layout,
                    estimated_size=self._estimate_content_size(current_group)
                )
                slides.append(mapped_slide)
                
                # Start new group
                current_group = group
                current_size = group_size
            else:
                # Add to current group
                current_group.extend(group)
                current_size += group_size
        
        # Add final group if any content remains
        if current_group:
            new_slide = SlideContent(
                title=slide.title if not slides else f"{slide.title} (cont.)",
                content=current_group,
                speaker_notes=slide.speaker_notes if not slides else "",
                slide_type=slide.slide_type,
                metadata=slide.metadata.copy()
            )
            
            mapped_slide = MappedSlide(
                content=new_slide,
                layout=layout,
                estimated_size=self._estimate_content_size(current_group)
            )
            slides.append(mapped_slide)
        
        return slides
    
    def _group_content_logically(self, content: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group content blocks into logical sections.
        
        Args:
            content: List of content blocks
            
        Returns:
            List of content groups
        """
        groups = []
        current_group = []
        
        for block in content:
            block_type = block.get("t", "")
            
            # Start new group for certain block types
            if block_type in ["Header", "HorizontalRule"] and current_group:
                groups.append(current_group)
                current_group = [block]
            
            # Keep related blocks together
            elif block_type in ["BulletList", "OrderedList", "Table", "CodeBlock"]:
                if current_group:
                    groups.append(current_group)
                current_group = [block]
                groups.append(current_group)
                current_group = []
            
            else:
                current_group.append(block)
        
        # Add final group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _chunk_content(
        self, 
        content: List[Dict[str, Any]], 
        chunk_size: int
    ) -> List[List[Dict[str, Any]]]:
        """Split content into chunks of specified size."""
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunks.append(content[i:i + chunk_size])
        return chunks
    
    def _estimate_content_size(self, content: List[Dict[str, Any]]) -> int:
        """Estimate the visual size of content for layout purposes."""
        size = 0
        for block in content:
            block_type = block.get("t", "")
            
            if block_type in ["Image", "Table", "CodeBlock"]:
                size += 3
            elif block_type in ["BulletList", "OrderedList"]:
                items = block.get("c", [])
                size += len(items) if isinstance(items, list) else 2
            else:
                size += 1
        
        return size