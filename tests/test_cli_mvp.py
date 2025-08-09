"""
Test CLI functionality for MarkDeck MVP.
"""

import json
import pytest
from pathlib import Path
import tempfile
import shutil
import subprocess
import os

# Import the standalone CLI components
from markdeck_cli import PandocBridge, PPTXGenerator, validate_theme_file, ParseError


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown():
    """Sample markdown content for testing."""
    return """# Welcome to MarkDeck

## Getting Started

This is a basic MarkDeck presentation.

- Create content in Markdown
- Build with `markdeck build`
- Customize with themes

::: notes
This is a speaker note that will be included in the presenter notes.
:::

## Code Example

```python
def hello():
    print("Hello, MarkDeck!")
```

## Next Steps

Run `markdeck build` to generate your first presentation!
"""


@pytest.fixture
def sample_theme():
    """Sample theme configuration for testing."""
    return {
        "fonts": {
            "heading": {"family": "Calibri", "size": 32, "color": "#1f4e79"},
            "body": {"family": "Calibri", "size": 18, "color": "#333333"},
            "code": {"family": "Consolas", "size": 14, "color": "#000000"}
        },
        "colors": {
            "primary": "#1f4e79",
            "secondary": "#70ad47",
            "background": "#ffffff",
            "text": "#333333"
        }
    }


@pytest.fixture
def schema_path():
    """Path to the theme schema."""
    return Path(__file__).parent.parent / "schemas" / "theme.schema.json"


def test_pandoc_detection():
    """Test pandoc detection."""
    # This will only work if pandoc is installed
    pandoc_path = shutil.which("pandoc")
    if pandoc_path:
        bridge = PandocBridge(pandoc_path)
        assert bridge.pandoc_path == pandoc_path
    else:
        # If pandoc is not installed, expect an error
        with pytest.raises((ParseError, FileNotFoundError)):
            PandocBridge()


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_markdown_to_ast(sample_markdown):
    """Test converting markdown to AST."""
    bridge = PandocBridge()
    ast = bridge.convert_to_ast(sample_markdown)
    
    # Check basic AST structure
    assert "blocks" in ast
    assert isinstance(ast["blocks"], list)
    assert len(ast["blocks"]) > 0
    
    # Check for headers
    headers = [block for block in ast["blocks"] if block.get("t") == "Header"]
    assert len(headers) >= 3  # We expect at least 3 headers


def test_theme_validation_valid(temp_dir, sample_theme, schema_path):
    """Test theme validation with valid theme."""
    if not schema_path.exists():
        pytest.skip("Schema file not found")
    
    theme_file = temp_dir / "valid_theme.json"
    with open(theme_file, 'w') as f:
        json.dump(sample_theme, f)
    
    assert validate_theme_file(theme_file) is True


def test_theme_validation_invalid(temp_dir, schema_path):
    """Test theme validation with invalid theme."""
    if not schema_path.exists():
        pytest.skip("Schema file not found")
    
    # Create invalid theme (missing required fields)
    invalid_theme = {"invalid": "theme"}
    theme_file = temp_dir / "invalid_theme.json"
    with open(theme_file, 'w') as f:
        json.dump(invalid_theme, f)
    
    assert validate_theme_file(theme_file) is False


def test_theme_validation_malformed_json(temp_dir):
    """Test theme validation with malformed JSON."""
    theme_file = temp_dir / "malformed_theme.json"
    theme_file.write_text("{ invalid json }")
    
    assert validate_theme_file(theme_file) is False


def test_theme_validation_missing_file(temp_dir):
    """Test theme validation with missing file."""
    missing_file = temp_dir / "missing_theme.json"
    assert validate_theme_file(missing_file) is False


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_pptx_generation(temp_dir, sample_markdown, sample_theme):
    """Test PowerPoint generation."""
    # Create markdown file
    md_file = temp_dir / "test.md"
    md_file.write_text(sample_markdown)
    
    # Create theme file
    theme_file = temp_dir / "theme.json"
    with open(theme_file, 'w') as f:
        json.dump(sample_theme, f)
    
    # Output file
    output_file = temp_dir / "test.pptx"
    
    # Convert markdown to AST
    bridge = PandocBridge()
    ast = bridge.convert_to_ast(sample_markdown)
    
    # Generate PowerPoint
    generator = PPTXGenerator()
    generator.generate(ast, output_file, sample_theme)
    
    # Check output file exists and has reasonable size
    assert output_file.exists()
    assert output_file.stat().st_size > 10000  # Should be at least 10KB


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_slide_parsing(sample_markdown):
    """Test parsing markdown into slides."""
    bridge = PandocBridge()
    ast = bridge.convert_to_ast(sample_markdown)
    
    generator = PPTXGenerator()
    slides = generator._parse_ast_to_slides(ast)
    
    # Should have multiple slides
    assert len(slides) >= 3
    
    # First slide should be title type (H1)
    assert slides[0].slide_type in ["title", "section"]
    assert "Welcome to MarkDeck" in slides[0].title
    
    # Should have slide with notes
    notes_slides = [s for s in slides if s.speaker_notes]
    assert len(notes_slides) > 0
    assert "speaker note" in notes_slides[0].speaker_notes


def test_text_extraction():
    """Test text extraction from Pandoc elements."""
    generator = PPTXGenerator()
    
    # Test inline text extraction
    inlines = [
        {"t": "Str", "c": "Hello"},
        {"t": "Space"},
        {"t": "Strong", "c": [{"t": "Str", "c": "world"}]},
        {"t": "Str", "c": "!"}
    ]
    
    text = generator._extract_text_from_inlines(inlines)
    assert "Hello" in text
    assert "world" in text
    
    # Test block text extraction
    blocks = [
        {
            "t": "Para",
            "c": [{"t": "Str", "c": "Test"}, {"t": "Space"}, {"t": "Str", "c": "paragraph"}]
        }
    ]
    
    text = generator._extract_text_from_blocks(blocks)
    assert "Test paragraph" in text


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_cli_integration(temp_dir):
    """Test CLI integration with subprocess."""
    cli_script = Path(__file__).parent.parent / "markdeck_cli.py"
    
    # Test init command
    result = subprocess.run([
        "python", str(cli_script), "init", "--dir", str(temp_dir)
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert (temp_dir / "examples" / "basic.md").exists()
    assert (temp_dir / "examples" / "theme.json").exists()
    
    # Test validate command
    result = subprocess.run([
        "python", str(cli_script), "validate", 
        "--theme", str(temp_dir / "examples" / "theme.json")
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "valid" in result.stdout
    
    # Test build command
    result = subprocess.run([
        "python", str(cli_script), "build",
        str(temp_dir / "examples" / "basic.md"),
        "--theme", str(temp_dir / "examples" / "theme.json"),
        "-o", str(temp_dir / "output.pptx")
    ], capture_output=True, text=True, cwd=str(temp_dir))
    
    assert result.returncode == 0
    assert (temp_dir / "output.pptx").exists()


if __name__ == "__main__":
    pytest.main([__file__])