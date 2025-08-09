"""
MarkDeck CLI Entry Point

Main command-line interface for MarkDeck presentation generation.
"""

import sys
from pathlib import Path
from typing import Optional
import shutil
import json

import typer
from rich.console import Console
from rich.table import Table
import jsonschema

app = typer.Typer(
    name="markdeck",
    help="Convert Markdown files to PowerPoint presentations",
    add_completion=False,
)
console = Console()


def detect_pandoc() -> str:
    """Detect if pandoc is installed and return path."""
    pandoc_path = shutil.which("pandoc")
    if not pandoc_path:
        console.print("[red]Error: Pandoc not found![/red]")
        console.print("\nPandoc is required for MarkDeck to work.")
        console.print("Please install Pandoc:")
        console.print("• Ubuntu/Debian: [bold]sudo apt install pandoc[/bold]")
        console.print("• macOS: [bold]brew install pandoc[/bold]")
        console.print("• Windows: [bold]choco install pandoc[/bold]")
        console.print("• Or download from: https://pandoc.org/installing.html")
        raise typer.Exit(1)
    return pandoc_path


def validate_theme_file(theme_path: Path) -> bool:
    """Validate a theme file against the schema."""
    try:
        # Load schema
        schema_path = Path(__file__).parent.parent.parent / "schemas" / "theme.schema.json"
        if not schema_path.exists():
            console.print(f"[red]Error: Schema not found at {schema_path}[/red]")
            return False
            
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Load theme
        with open(theme_path) as f:
            theme = json.load(f)
        
        # Validate
        jsonschema.validate(theme, schema)
        return True
        
    except FileNotFoundError:
        console.print(f"[red]Error: Theme file not found: {theme_path}[/red]")
        return False
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in theme file: {e}[/red]")
        return False
    except jsonschema.ValidationError as e:
        console.print(f"[red]Error: Theme validation failed: {e.message}[/red]")
        if e.absolute_path:
            console.print(f"[red]Path: {'.'.join(map(str, e.absolute_path))}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


@app.command()
def build(
    input_file: Path = typer.Argument(..., help="Input Markdown file"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output PowerPoint file"),
    theme: Optional[Path] = typer.Option(None, "--theme", help="Theme JSON file"),
    template: Optional[Path] = typer.Option(None, "--template", help="PowerPoint template file"),
    config: Optional[Path] = typer.Option(None, "--config", help="Config file (markdeck.toml/yaml)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Build a PowerPoint presentation from Markdown."""
    
    if verbose:
        console.print(f"[blue]Building presentation from {input_file}[/blue]")
    
    # Check if input file exists
    if not input_file.exists():
        console.print(f"[red]Error: Input file not found: {input_file}[/red]")
        raise typer.Exit(1)
    
    # Determine output path
    if output is None:
        output = input_file.with_suffix(".pptx")
    
    # Detect pandoc
    pandoc_path = detect_pandoc()
    
    # Validate theme if provided
    if theme and not validate_theme_file(theme):
        raise typer.Exit(1)
    
    try:
        # Import components directly without going through __init__.py
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from parsers.pandoc_bridge import PandocBridge
        from generators.pptx_generator import PPTXGenerator
        
        # Initialize components
        bridge = PandocBridge(pandoc_path)
        generator = PPTXGenerator()
        
        # Read and parse markdown
        content = input_file.read_text(encoding='utf-8')
        if verbose:
            console.print("[blue]Parsing Markdown with Pandoc...[/blue]")
        
        ast = bridge.convert_to_ast(content)
        
        # Load theme if provided
        theme_config = None
        if theme:
            with open(theme) as f:
                theme_config = json.load(f)
        
        # Generate presentation
        if verbose:
            console.print("[blue]Generating PowerPoint presentation...[/blue]")
        
        generator.generate(ast, output, theme_config, template)
        
        console.print(f"[green]✓ Generated presentation: {output}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", help="Overwrite existing files"),
    directory: Path = typer.Option(Path("."), "--dir", help="Directory to create files in"),
):
    """Initialize example files in the current directory."""
    
    # Create examples directory if it doesn't exist
    examples_dir = directory / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # Paths for example files
    basic_md = examples_dir / "basic.md"
    theme_json = examples_dir / "theme.json"
    
    # Check for existing files
    if basic_md.exists() and not force:
        console.print(f"[yellow]Warning: {basic_md} already exists. Use --force to overwrite.[/yellow]")
    if theme_json.exists() and not force:
        console.print(f"[yellow]Warning: {theme_json} already exists. Use --force to overwrite.[/yellow]")
    
    if (basic_md.exists() or theme_json.exists()) and not force:
        console.print("[yellow]Use --force to overwrite existing files.[/yellow]")
        raise typer.Exit(1)
    
    try:
        # Get source files from package
        source_dir = Path(__file__).parent.parent / "examples"
        
        # Copy basic.md
        if source_dir.exists():
            source_basic = source_dir / "basic.md"
            source_theme = source_dir / "theme.json"
            
            if source_basic.exists():
                shutil.copy2(source_basic, basic_md)
                console.print(f"[green]✓ Created {basic_md}[/green]")
            
            if source_theme.exists():
                shutil.copy2(source_theme, theme_json)
                console.print(f"[green]✓ Created {theme_json}[/green]")
        else:
            # Fallback: create minimal examples
            basic_content = """# Welcome to MarkDeck

## Getting Started

This is a basic MarkDeck presentation.

- Create content in Markdown
- Build with `markdeck build`
- Customize with themes

::: notes
This is a speaker note that will be included in the presenter notes.
:::

## Next Steps

Run `markdeck build examples/basic.md` to generate your first presentation!
"""
            basic_md.write_text(basic_content)
            console.print(f"[green]✓ Created {basic_md}[/green]")
            
            theme_content = """{
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
}"""
            theme_json.write_text(theme_content)
            console.print(f"[green]✓ Created {theme_json}[/green]")
            
        console.print("\n[blue]Example files created! Try:[/blue]")
        console.print(f"[bold]markdeck build {basic_md} --theme {theme_json}[/bold]")
        
    except Exception as e:
        console.print(f"[red]Error creating example files: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    theme: Path = typer.Option(..., "--theme", help="Theme JSON file to validate"),
):
    """Validate a theme configuration file."""
    
    console.print(f"[blue]Validating theme: {theme}[/blue]")
    
    if validate_theme_file(theme):
        console.print(f"[green]✓ Theme {theme} is valid![/green]")
    else:
        raise typer.Exit(1)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", callback=lambda x: x, is_eager=True, help="Show version"),
):
    """MarkDeck: Convert Markdown to PowerPoint presentations."""
    if version:
        console.print("MarkDeck 0.1.0")
        raise typer.Exit()


if __name__ == "__main__":
    app()