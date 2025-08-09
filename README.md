# MarkDeck

A command-line tool that converts Markdown files into professional PowerPoint presentations using Pandoc JSON AST parsing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Markdown to PowerPoint**: Convert Markdown files to professional PPTX presentations
- **Pandoc Integration**: Robust Markdown parsing with Pandoc JSON AST
- **Theme System**: JSON-based theming with fonts, colors, and layouts
- **Speaker Notes**: Extract speaker notes from fenced divs (`::: notes`)
- **CLI Commands**: Build, init, and validate commands
- **Schema Validation**: Validate themes against JSON schema

## Quick Start

### Prerequisites

**Install Pandoc** (required):
- **Ubuntu/Debian**: `sudo apt install pandoc`
- **macOS**: `brew install pandoc`
- **Windows**: `choco install pandoc`
- **Or download from**: https://pandoc.org/installing.html

**Install Python dependencies**:
```bash
pip install python-pptx jsonschema typer rich pyyaml toml
```

### Basic Usage

1. **Initialize example files**:
```bash
python markdeck_cli.py init
```

2. **Build a presentation**:
```bash
python markdeck_cli.py build examples/basic.md --theme examples/theme.json
```

3. **Validate a theme**:
```bash
python markdeck_cli.py validate --theme examples/theme.json
```

### Example Markdown

```markdown
# Welcome to MarkDeck
## Converting Markdown to PowerPoint Made Easy

::: notes
This is a speaker note that will appear in presenter notes.
:::

## Key Features

- **Easy to use**: Simple Markdown syntax
- **Professional output**: Beautiful PowerPoint presentations
- **Flexible theming**: Customize the look and feel
- **Speaker notes**: Add notes for presenters

## Code Example

```python
def hello_world():
    print("Hello, MarkDeck!")
```

## Getting Started

1. Write your content in Markdown
2. Choose a theme (or create your own)
3. Run MarkDeck to generate your presentation
4. Present with confidence!
```

### Example Theme

```json
{
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
```

## CLI Commands

### Build Command

Convert Markdown to PowerPoint:

```bash
python markdeck_cli.py build input.md [OPTIONS]
```

**Options:**
- `-o, --output PATH`: Output PowerPoint file
- `--theme PATH`: Theme JSON file  
- `--template PATH`: PowerPoint template file
- `--config PATH`: Config file (markdeck.toml/yaml)
- `-v, --verbose`: Verbose output

**Examples:**
```bash
# Basic usage
python markdeck_cli.py build presentation.md

# With custom theme and output
python markdeck_cli.py build presentation.md --theme corporate.json -o slides.pptx

# Verbose output
python markdeck_cli.py build presentation.md --verbose
```

### Init Command

Create example files:

```bash
python markdeck_cli.py init [OPTIONS]
```

**Options:**
- `--force`: Overwrite existing files
- `--dir PATH`: Directory to create files in

**Examples:**
```bash
# Create examples in current directory
python markdeck_cli.py init

# Force overwrite existing files
python markdeck_cli.py init --force
```

### Validate Command

Validate theme configuration:

```bash
python markdeck_cli.py validate --theme theme.json
```

## Markdown Features

### Slide Structure

- **H1 headings** (`#`) create section slides or title slide (if first)
- **H2 headings** (`##`) create content slides
- **Horizontal rules** (`---`) create slide breaks

### Content Types

- **Paragraphs**: Regular text content
- **Bullet Lists**: Unordered and ordered lists
- **Code Blocks**: Formatted with monospace font
- **Images**: Placeholder support (full image support planned)

### Speaker Notes

Use fenced divs to add speaker notes:

```markdown
## Slide Title

Slide content here.

::: notes
This is a speaker note that will appear in presenter notes but not on the slide.
:::
```

## Theme System

### Theme Structure

Themes are JSON files validated against a schema:

```json
{
  "fonts": {
    "heading": {"family": "string", "size": number, "color": "#hex"},
    "body": {"family": "string", "size": number, "color": "#hex"},
    "code": {"family": "string", "size": number, "color": "#hex"}
  },
  "colors": {
    "primary": "#hex",
    "secondary": "#hex", 
    "background": "#hex",
    "text": "#hex"
  },
  "layouts": {
    "title": number,
    "title_content": number,
    "section": number
  }
}
```

### Creating Custom Themes

1. Start with the example theme from `markdeck_cli.py init`
2. Modify fonts, colors, and layouts
3. Validate with `markdeck_cli.py validate --theme your_theme.json`
4. Use with `markdeck_cli.py build --theme your_theme.json`

## Architecture

MarkDeck follows a simple, modular architecture:

```
Markdown Input
    ↓
Pandoc (JSON AST)
    ↓
Slide Parser
    ↓
Theme Application
    ↓
PowerPoint Generation (python-pptx)
    ↓
PPTX Output
```

### Key Components

1. **Pandoc Bridge**: Converts Markdown to JSON AST using Pandoc
2. **Slide Parser**: Processes AST into slide structure
3. **Theme Engine**: Applies styling from JSON theme
4. **PPTX Generator**: Creates PowerPoint files using python-pptx

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
python -m pytest tests/test_cli_mvp.py -v
```

### Project Structure

```
MarkDeck/
├── markdeck_cli.py          # Standalone CLI implementation
├── examples/                # Example files
│   ├── basic.md            # Sample Markdown presentation
│   └── theme.json          # Sample theme configuration
├── schemas/                 # JSON schemas
│   └── theme.schema.json   # Theme validation schema
├── tests/                   # Test suite
│   └── test_cli_mvp.py     # MVP functionality tests
└── .github/workflows/      # CI/CD configuration
    └── ci.yml              # GitHub Actions workflow
```

## Troubleshooting

### Pandoc Not Found

If you get a "Pandoc not found" error:

1. **Check installation**: `pandoc --version`
2. **Install Pandoc**: Follow installation instructions above
3. **Check PATH**: Ensure pandoc is in your system PATH

### Theme Validation Errors

If theme validation fails:

1. **Check JSON syntax**: Ensure valid JSON format
2. **Required fields**: Include `fonts` and `colors` sections
3. **Color format**: Use hex colors like `#1f4e79`
4. **Run validate**: `markdeck_cli.py validate --theme theme.json`

### PowerPoint Generation Issues

If PPTX generation fails:

1. **Check permissions**: Ensure write access to output directory
2. **Template file**: Verify template file exists (if using `--template`)
3. **Dependencies**: Ensure `python-pptx` is installed

## Roadmap

### Current (MVP)
- [x] Core Markdown to PowerPoint conversion
- [x] Basic theming system
- [x] CLI interface (build, init, validate)
- [x] Pandoc integration with JSON AST
- [x] Speaker notes support
- [x] Theme validation
- [x] Example files and documentation

### Future Enhancements
- [ ] PDF export support
- [ ] Plugin system for extensibility
- [ ] Advanced image handling
- [ ] Table support
- [ ] Custom slide layouts
- [ ] Animation support
- [ ] Web-based theme editor

## Contributing

We welcome contributions! To get started:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Pandoc**: For excellent Markdown parsing capabilities
- **python-pptx**: For PowerPoint file generation
- **Typer**: For the CLI framework
- **Rich**: For beautiful terminal output
