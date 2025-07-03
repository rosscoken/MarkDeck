"""
Unit tests for MarkDeck parsers.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from markdeck.parsers.markdown import MarkdownParser, SlideContent, ParsedDocument
from markdeck.parsers.pandoc_bridge import PandocBridge
from markdeck.parsers.slide_mapper import SlideMapper, SlideLayout, MappedSlide
from markdeck.core.exceptions import ParseError


class TestMarkdownParser:
    """Test cases for MarkdownParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = MarkdownParser()
        
        # Sample Pandoc AST for testing
        self.sample_ast = {
            "pandoc-api-version": [1, 22, 2],
            "meta": {
                "title": {"t": "MetaString", "c": "Test Presentation"},
                "author": {"t": "MetaString", "c": "Test Author"}
            },
            "blocks": [
                {
                    "t": "Header",
                    "c": [1, [], [{"t": "Str", "c": "Title"}, {"t": "Space"}, {"t": "Str", "c": "Slide"}]]
                },
                {
                    "t": "Para",
                    "c": [{"t": "Str", "c": "This"}, {"t": "Space"}, {"t": "Str", "c": "is"}, {"t": "Space"}, {"t": "Str", "c": "content."}]
                },
                {
                    "t": "HorizontalRule"
                },
                {
                    "t": "Header",
                    "c": [2, [], [{"t": "Str", "c": "Second"}, {"t": "Space"}, {"t": "Str", "c": "Slide"}]]
                },
                {
                    "t": "BulletList",
                    "c": [
                        [{"t": "Para", "c": [{"t": "Str", "c": "Item"}, {"t": "Space"}, {"t": "Str", "c": "1"}]}],
                        [{"t": "Para", "c": [{"t": "Str", "c": "Item"}, {"t": "Space"}, {"t": "Str", "c": "2"}]}]
                    ]
                }
            ]
        }
    
    def test_init(self):
        """Test parser initialization."""
        config = {"slide_break_pattern": r"^===\s*$"}
        plugins = [Mock()]
        
        parser = MarkdownParser(config=config, plugins=plugins)
        
        assert parser.config == config
        assert parser.plugins == plugins
        assert parser.slide_break_pattern == r"^===\s*$"
    
    def test_extract_speaker_notes(self):
        """Test speaker notes extraction."""
        content = """# Title

Some content here.

<!-- Speaker note: This is a note -->

More content.

<!-- Speaker note: Another note -->
"""
        
        cleaned_content, notes_map = self.parser._extract_speaker_notes(content)
        
        assert len(notes_map) == 2
        assert "This is a note" in notes_map.values()
        assert "Another note" in notes_map.values()
        assert "<!-- Speaker note:" not in cleaned_content
    
    def test_extract_text_from_inlines(self):
        """Test text extraction from inline elements."""
        inlines = [
            {"t": "Str", "c": "Hello"},
            {"t": "Space"},
            {"t": "Strong", "c": [{"t": "Str", "c": "world"}]},
            {"t": "Str", "c": "!"}
        ]
        
        text = self.parser._extract_text_from_inlines(inlines)
        assert text == "Hello world!"
    
    def test_extract_document_metadata(self):
        """Test document metadata extraction."""
        metadata = self.parser._extract_document_metadata(self.sample_ast)
        
        assert metadata["title"] == "Test Presentation"
        assert metadata["author"] == "Test Author"
    
    def test_split_into_slides(self):
        """Test splitting AST into slides."""
        slides = self.parser._split_into_slides(self.sample_ast, {})
        
        assert len(slides) == 2
        assert slides[0].title == "Title Slide"
        assert slides[0].slide_type == "title"
        assert slides[1].title == "Second Slide"
        assert slides[1].slide_type == "section"
        assert len(slides[1].content) == 1  # BulletList
    
    @patch('subprocess.run')
    def test_parse_with_pandoc_success(self, mock_run):
        """Test successful Pandoc parsing."""
        mock_run.return_value = Mock(
            stdout=json.dumps(self.sample_ast),
            stderr="",
            returncode=0
        )
        
        result = self.parser._parse_with_pandoc("# Test")
        
        assert result == self.sample_ast
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_parse_with_pandoc_failure(self, mock_run):
        """Test Pandoc parsing failure."""
        mock_run.side_effect = Exception("Pandoc failed")
        
        with pytest.raises(ParseError):
            self.parser._parse_with_pandoc("# Test")
    
    @patch('markdeck.parsers.markdown.MarkdownParser._parse_with_pandoc')
    def test_parse_content_success(self, mock_pandoc):
        """Test successful content parsing."""
        mock_pandoc.return_value = self.sample_ast
        
        content = """# Title Slide

Content here.

<!-- Speaker note: Test note -->

---

## Second Slide

- Item 1
- Item 2
"""
        
        result = self.parser.parse_content(content)
        
        assert isinstance(result, ParsedDocument)
        assert len(result.structure) > 0
        assert result.metadata["title"] == "Test Presentation"
        assert result.raw_ast == self.sample_ast
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        with pytest.raises(ParseError):
            self.parser.parse_file(Path("nonexistent.md"))
    
    @patch('pathlib.Path.read_text')
    @patch('markdeck.parsers.markdown.MarkdownParser.parse_content')
    def test_parse_file_success(self, mock_parse_content, mock_read_text):
        """Test successful file parsing."""
        mock_read_text.return_value = "# Test"
        mock_parse_content.return_value = ParsedDocument()
        
        result = self.parser.parse_file(Path("test.md"))
        
        assert isinstance(result, ParsedDocument)
        mock_read_text.assert_called_once()
        mock_parse_content.assert_called_once_with("# Test", "test.md")


class TestPandocBridge:
    """Test cases for PandocBridge."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="pandoc 3.0.0")
            self.bridge = PandocBridge()
    
    @patch('subprocess.run')
    def test_verify_pandoc_success(self, mock_run):
        """Test successful Pandoc verification."""
        mock_run.return_value = Mock(stdout="pandoc 3.0.0\n")
        
        # Should not raise exception
        bridge = PandocBridge()
        assert bridge.pandoc_path == "pandoc"
    
    @patch('subprocess.run')
    def test_verify_pandoc_failure(self, mock_run):
        """Test Pandoc verification failure."""
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(ParseError):
            PandocBridge()
    
    @patch('subprocess.run')
    def test_convert_to_ast_success(self, mock_run):
        """Test successful AST conversion."""
        sample_ast = {"pandoc-api-version": [1, 22, 2], "blocks": []}
        mock_run.return_value = Mock(
            stdout=json.dumps(sample_ast),
            stderr="",
            returncode=0
        )
        
        result = self.bridge.convert_to_ast("# Test")
        
        assert result == sample_ast
    
    @patch('subprocess.run')
    def test_convert_to_ast_failure(self, mock_run):
        """Test AST conversion failure."""
        mock_run.side_effect = Exception("Conversion failed")
        
        with pytest.raises(ParseError):
            self.bridge.convert_to_ast("# Test")
    
    def test_extract_text_from_inlines(self):
        """Test text extraction from inlines."""
        inlines = [
            {"t": "Str", "c": "Hello"},
            {"t": "Space"},
            {"t": "Str", "c": "world"}
        ]
        
        text = self.bridge.extract_text_from_inlines(inlines)
        assert text == "Hello world"
    
    def test_extract_text_from_blocks(self):
        """Test text extraction from blocks."""
        blocks = [
            {
                "t": "Header",
                "c": [1, [], [{"t": "Str", "c": "Title"}]]
            },
            {
                "t": "Para",
                "c": [{"t": "Str", "c": "Content"}]
            }
        ]
        
        text = self.bridge.extract_text_from_blocks(blocks)
        assert "Title" in text
        assert "Content" in text
    
    def test_find_elements_by_type(self):
        """Test finding elements by type."""
        ast = {
            "blocks": [
                {"t": "Header", "c": [1, [], []]},
                {"t": "Para", "c": []},
                {"t": "Image", "c": [[], [], ["", ""]]},
                {"t": "Para", "c": []}
            ]
        }
        
        headers = self.bridge.find_elements_by_type(ast, "Header")
        images = self.bridge.find_elements_by_type(ast, "Image")
        
        assert len(headers) == 1
        assert len(images) == 1
    
    def test_validate_ast_valid(self):
        """Test AST validation with valid AST."""
        valid_ast = {
            "pandoc-api-version": [1, 22, 2],
            "blocks": []
        }
        
        assert self.bridge.validate_ast(valid_ast) is True
    
    def test_validate_ast_invalid(self):
        """Test AST validation with invalid AST."""
        invalid_ast = {"invalid": "structure"}
        
        assert self.bridge.validate_ast(invalid_ast) is False


class TestSlideMapper:
    """Test cases for SlideMapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = SlideMapper()
        
        # Sample slides for testing
        self.sample_slides = [
            SlideContent(
                title="Title Slide",
                content=[
                    {"t": "Para", "c": [{"t": "Str", "c": "Introduction"}]}
                ],
                slide_type="title"
            ),
            SlideContent(
                title="Content Slide",
                content=[
                    {"t": "Para", "c": [{"t": "Str", "c": "Content"}]},
                    {"t": "BulletList", "c": [
                        [{"t": "Para", "c": [{"t": "Str", "c": "Item 1"}]}],
                        [{"t": "Para", "c": [{"t": "Str", "c": "Item 2"}]}]
                    ]},
                    {"t": "Image", "c": [[], [], ["image.png", ""]]},
                ],
                slide_type="content"
            )
        ]
    
    def test_init(self):
        """Test mapper initialization."""
        config = {"max_content_per_slide": 5}
        mapper = SlideMapper(config=config)
        
        assert mapper.config == config
        assert mapper.max_content_per_slide == 5
    
    def test_analyze_content(self):
        """Test content analysis."""
        content = [
            {"t": "Para", "c": []},
            {"t": "Image", "c": [[], [], ["", ""]]},
            {"t": "CodeBlock", "c": [[], "code"]},
            {"t": "BulletList", "c": [[]]},
            {"t": "Table", "c": []}
        ]
        
        analysis = self.mapper._analyze_content(content)
        
        assert analysis["block_count"] == 5
        assert analysis["has_images"] is True
        assert analysis["image_count"] == 1
        assert analysis["has_code_blocks"] is True
        assert analysis["code_block_count"] == 1
        assert analysis["has_tables"] is True
        assert analysis["table_count"] == 1
        assert analysis["has_lists"] is True
        assert analysis["list_count"] == 1
    
    def test_select_layout_title(self):
        """Test layout selection for title slide."""
        slide = SlideContent(title="Title", slide_type="title")
        layout = self.mapper._select_layout(slide)
        
        assert layout.layout_type == "title"
    
    def test_select_layout_content_with_images(self):
        """Test layout selection for content with images."""
        slide = SlideContent(
            title="Content",
            content=[{"t": "Image", "c": [[], [], ["", ""]]}],
            slide_type="content"
        )
        layout = self.mapper._select_layout(slide)
        
        assert layout.layout_type == "content_image"
    
    def test_select_layout_content_with_code(self):
        """Test layout selection for content with code."""
        slide = SlideContent(
            title="Content",
            content=[{"t": "CodeBlock", "c": [[], "code"]}],
            slide_type="content"
        )
        layout = self.mapper._select_layout(slide)
        
        assert layout.layout_type == "content_code"
    
    def test_map_slides_simple(self):
        """Test simple slide mapping."""
        mapped_slides = self.mapper.map_slides(self.sample_slides)
        
        assert len(mapped_slides) >= len(self.sample_slides)
        assert all(isinstance(slide, MappedSlide) for slide in mapped_slides)
        assert mapped_slides[0].layout.layout_type == "title"
        assert mapped_slides[1].layout.layout_type == "content_image"
    
    def test_distribute_content_fits(self):
        """Test content distribution when content fits."""
        slide = SlideContent(
            title="Test",
            content=[{"t": "Para", "c": []}],
            slide_type="content"
        )
        layout = SlideLayout("content", max_content_blocks=5)
        
        distributed = self.mapper._distribute_content(slide, layout)
        
        assert len(distributed) == 1
        assert len(distributed[0].overflow_content) == 0
    
    def test_distribute_content_overflow(self):
        """Test content distribution with overflow."""
        # Create slide with more content than layout allows
        content = [{"t": "Para", "c": []} for _ in range(10)]
        slide = SlideContent(
            title="Test",
            content=content,
            slide_type="content"
        )
        layout = SlideLayout("content", max_content_blocks=3)
        
        # Disable auto-split for this test
        mapper = SlideMapper({"auto_split_large_content": False})
        distributed = mapper._distribute_content(slide, layout)
        
        assert len(distributed) == 1
        assert len(distributed[0].content.content) == 3
        assert len(distributed[0].overflow_content) == 7
    
    def test_split_content_auto(self):
        """Test automatic content splitting."""
        # Create slide with content that needs splitting
        content = [{"t": "Para", "c": []} for _ in range(10)]
        slide = SlideContent(
            title="Test",
            content=content,
            slide_type="content"
        )
        layout = SlideLayout("content", max_content_blocks=4, content_distribution="auto")
        
        split_slides = self.mapper._split_content(slide, layout)
        
        assert len(split_slides) > 1
        # Check that content is distributed
        total_content = sum(len(s.content.content) for s in split_slides)
        assert total_content == 10
    
    def test_chunk_content(self):
        """Test content chunking."""
        content = [{"t": "Para", "c": []} for _ in range(7)]
        chunks = self.mapper._chunk_content(content, 3)
        
        assert len(chunks) == 3
        assert len(chunks[0]) == 3
        assert len(chunks[1]) == 3
        assert len(chunks[2]) == 1
    
    def test_estimate_content_size(self):
        """Test content size estimation."""
        content = [
            {"t": "Para", "c": []},  # size 1
            {"t": "Image", "c": []},  # size 3
            {"t": "BulletList", "c": [[], []]},  # size 2 (2 items)
        ]
        
        size = self.mapper._estimate_content_size(content)
        assert size == 6
    
    def test_group_content_logically(self):
        """Test logical content grouping."""
        content = [
            {"t": "Para", "c": []},
            {"t": "Para", "c": []},
            {"t": "BulletList", "c": []},
            {"t": "Para", "c": []},
            {"t": "Header", "c": [2, [], []]},
            {"t": "Para", "c": []}
        ]
        
        groups = self.mapper._group_content_logically(content)
        
        # Should group paragraphs together, separate lists, and start new groups at headers
        assert len(groups) >= 3


class TestSlideContent:
    """Test cases for SlideContent dataclass."""
    
    def test_slide_content_creation(self):
        """Test SlideContent creation."""
        slide = SlideContent(
            title="Test Slide",
            content=[{"t": "Para", "c": []}],
            speaker_notes="Test notes",
            slide_type="content"
        )
        
        assert slide.title == "Test Slide"
        assert len(slide.content) == 1
        assert slide.speaker_notes == "Test notes"
        assert slide.slide_type == "content"
        assert isinstance(slide.metadata, dict)
    
    def test_slide_content_defaults(self):
        """Test SlideContent default values."""
        slide = SlideContent()
        
        assert slide.title == ""
        assert slide.content == []
        assert slide.speaker_notes == ""
        assert slide.slide_type == "content"
        assert slide.metadata == {}


class TestParsedDocument:
    """Test cases for ParsedDocument dataclass."""
    
    def test_parsed_document_creation(self):
        """Test ParsedDocument creation."""
        slides = [SlideContent(title="Test")]
        metadata = {"title": "Test Presentation"}
        raw_ast = {"blocks": []}
        
        doc = ParsedDocument(
            structure=slides,
            metadata=metadata,
            raw_ast=raw_ast
        )
        
        assert doc.structure == slides
        assert doc.metadata == metadata
        assert doc.raw_ast == raw_ast
        assert doc.errors == []
    
    def test_parsed_document_defaults(self):
        """Test ParsedDocument default values."""
        doc = ParsedDocument()
        
        assert doc.structure == []
        assert doc.metadata == {}
        assert doc.raw_ast == {}
        assert doc.errors == []


# Integration tests
class TestParserIntegration:
    """Integration tests for parser components."""
    
    @patch('subprocess.run')
    def test_end_to_end_parsing(self, mock_run):
        """Test end-to-end parsing workflow."""
        # Mock Pandoc response
        sample_ast = {
            "pandoc-api-version": [1, 22, 2],
            "meta": {"title": {"t": "MetaString", "c": "Test"}},
            "blocks": [
                {
                    "t": "Header",
                    "c": [1, [], [{"t": "Str", "c": "Title"}]]
                },
                {
                    "t": "Para",
                    "c": [{"t": "Str", "c": "Content"}]
                },
                {
                    "t": "HorizontalRule"
                },
                {
                    "t": "Header",
                    "c": [2, [], [{"t": "Str", "c": "Section"}]]
                }
            ]
        }
        
        mock_run.return_value = Mock(
            stdout=json.dumps(sample_ast),
            stderr="",
            returncode=0
        )
        
        # Create parser and mapper
        parser = MarkdownParser()
        mapper = SlideMapper()
        
        # Parse content
        content = """# Title

Content here.

<!-- Speaker note: Test note -->

---

## Section
"""
        
        parsed_doc = parser.parse_content(content)
        mapped_slides = mapper.map_slides(parsed_doc.structure)
        
        # Verify results
        assert len(parsed_doc.structure) == 2
        assert parsed_doc.metadata["title"] == "Test"
        assert len(mapped_slides) >= 2
        assert all(isinstance(slide, MappedSlide) for slide in mapped_slides)


if __name__ == "__main__":
    pytest.main([__file__])