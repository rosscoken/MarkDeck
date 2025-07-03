"""
MarkDeck CLI Entry Point

Main command-line interface for MarkDeck presentation generation.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from markdeck import __version__
from markdeck.core.engine import MarkDeckEngine
from markdeck.core.exceptions import MarkDeckError
from markdeck.utils.logging import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="markdeck",
        description="Convert Markdown files to PowerPoint presentations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  markdeck presentation.md
  markdeck presentation.md --theme corporate --output slides.pptx
  markdeck presentation.md --pdf --theme-dir ./themes
        """,
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input Markdown file",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path (default: same as input with .pptx extension)",
    )

    parser.add_argument(
        "-t", "--theme",
        type=str,
        default="default",
        help="Theme name or path to theme file (default: default)",
    )

    parser.add_argument(
        "--theme-dir",
        type=Path,
        help="Directory containing theme files",
    )

    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also export to PDF",
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Configuration file path",
    )

    parser.add_argument(
        "--plugins-dir",
        type=Path,
        help="Directory containing plugins",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (use -v, -vv, or -vvv)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"MarkDeck {__version__}",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate without generating output",
    )

    parser.add_argument(
        "--validate-theme",
        action="store_true",
        help="Validate theme configuration and exit",
    )

    return parser


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the MarkDeck CLI.
    
    Args:
        argv: Command line arguments (defaults to sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging based on verbosity
    setup_logging(args.verbose)

    try:
        # Initialize the MarkDeck engine
        engine = MarkDeckEngine(
            config_path=args.config,
            plugins_dir=args.plugins_dir,
        )

        # Validate theme if requested
        if args.validate_theme:
            engine.validate_theme(args.theme, args.theme_dir)
            print(f"Theme '{args.theme}' is valid")
            return 0

        # Determine output path
        output_path = args.output
        if output_path is None:
            output_path = args.input.with_suffix(".pptx")

        # Process the presentation
        result = engine.process(
            input_path=args.input,
            output_path=output_path,
            theme=args.theme,
            theme_dir=args.theme_dir,
            export_pdf=args.pdf,
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print(f"Dry run completed successfully")
            print(f"Would generate: {output_path}")
            if args.pdf:
                pdf_path = output_path.with_suffix(".pdf")
                print(f"Would also export: {pdf_path}")
        else:
            print(f"Generated: {result.output_path}")
            if result.pdf_path:
                print(f"Exported PDF: {result.pdf_path}")

        return 0

    except MarkDeckError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())